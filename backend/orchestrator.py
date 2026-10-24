"""Audit Orchestrator, TinyFish Adapter, Evidence Normaliser & Safety Gate (Boxes B, D, E)."""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, AsyncIterator
from urllib.parse import urlparse

from mock_data import (
    mock_report,
    mock_step_event,
    mock_steps_for_run,
    now,
    resolve_preset_demo_path,
)
from models import (
    AuditOutcome,
    CcpaAlignment,
    CcpaPattern,
    Evidence,
    FrictionIndicator,
    FrictionSignal,
    Report,
    RunEvent,
    StopReason,
)
from scoring import INDICATOR_SEVERITY, score_signals

VALID_INDICATORS: set[str] = {
    "extra_steps",
    "hidden_cancel",
    "redirects",
    "forced_reason",
    "retention_offer",
    "unclear_copy",
}

VALID_CCPA: set[str] = {
    "false_urgency",
    "basket_sneaking",
    "confirm_shaming",
    "forced_action",
    "subscription_trap",
    "interface_interference",
    "bait_and_switch",
    "drip_pricing",
    "disguised_advertisement",
    "nagging",
    "trick_question",
    "saas_billing",
    "rogue_malwares",
}

INDICATOR_TO_DEFAULT_CCPA: dict[FrictionIndicator, CcpaPattern] = {
    "extra_steps": "subscription_trap",
    "hidden_cancel": "interface_interference",
    "redirects": "subscription_trap",
    "forced_reason": "forced_action",
    "retention_offer": "nagging",
    "unclear_copy": "confirm_shaming",
}

BLOCK_KEYWORDS = (
    "error 1200",
    "cloudflare",
    "captcha",
    "verify you are human",
    "access denied",
    "bot detection",
    "attention required",
    "login required",
    "sign in to continue",
)

NEGATED_BARRIER_PHRASES = (
    "no captcha",
    "no cloudflare",
    "without captcha",
    "without cloudflare",
    "no login wall",
    "not blocked",
)

META_STEP_PREFIXES = (
    "submit cancellation",
    "submit audit",
    "get full page content",
    "capture full",
    "compile ",
    "return json",
)

CCPA_DEFAULT_RATIONALES: dict[CcpaPattern, str] = {
    "subscription_trap": "Cancellation requires navigating a multi-step buried path instead of a direct exit control.",
    "interface_interference": "Visual hierarchy strongly favours keeping the plan over a de-emphasized cancellation control.",
    "confirm_shaming": "Confirmation copy uses guilt or emotional manipulation to steer the user away from cancelling.",
    "nagging": "Retention or discount interstitials repeatedly interrupt the user's explicit intent to cancel.",
    "forced_action": "User is forced to complete a mandatory survey or extra action before proceeding with cancellation.",
    "false_urgency": "Time-limited or pressure messaging is used during the cancellation flow to deter exit.",
    "trick_question": "Confusing or ambiguous button labels make it unclear which option continues cancellation.",
    "basket_sneaking": "Unexpected add-on or renewal terms surfaced during subscription management.",
    "bait_and_switch": "Promised cancellation action redirects to a different outcome or plan change.",
    "drip_pricing": "Additional fees or penalties are revealed only at the cancellation stage.",
    "disguised_advertisement": "Promotional retention offers are disguised as primary navigation controls.",
    "saas_billing": "Opaque billing or renewal terms obstruct straightforward subscription exit.",
    "rogue_malwares": "Deceptive popups or redirects interfere with account management.",
}

# Documentation placeholder/local hosts default to the fast deterministic mock path
DEMO_FALLBACK_HOSTS = {"example.in", "www.example.in", "example.com", "www.example.com", "localhost", "127.0.0.1"}


def resolve_effective_start_url(service: str, start_url: str | None) -> str | None:
    """Resolve `start_url`, or map preset service names to `PUBLIC_DEMO_BASE_URL` when configured."""
    if start_url:
        host = (urlparse(start_url).hostname or "").lower()
        if host and host not in DEMO_FALLBACK_HOSTS:
            return start_url
    public_base = (os.getenv("PUBLIC_DEMO_BASE_URL") or "").strip().rstrip("/")
    if public_base.startswith("https://"):
        demo_path = resolve_preset_demo_path(service, start_url)
        return f"{public_base}{demo_path}"
    return start_url


def should_use_live_tinyfish(start_url: str | None, service: str = "") -> bool:
    """Return True only when a real external target URL (or PUBLIC_DEMO_BASE_URL) and TINYFISH_API_KEY are present."""
    effective_url = resolve_effective_start_url(service, start_url)
    if not effective_url or not os.getenv("TINYFISH_API_KEY"):
        return False
    host = (urlparse(effective_url).hostname or "").lower()
    return bool(host) and host not in DEMO_FALLBACK_HOSTS


def build_audit_goal(service: str) -> str:
    return (
        f"You are auditing the subscription cancellation journey for '{service}' in India. "
        "Navigate toward cancelling the subscription and observe every step, dark pattern, or barrier. "
        "CRITICAL SAFETY RULE: STOP BEFORE clicking any final 'Cancel subscription' or 'Confirm cancellation' button. "
        "Never complete an irreversible cancellation. "
        "If you hit a CAPTCHA, Cloudflare block, OTP gate, or login wall that you cannot pass, stop immediately and set blocked=true. "
        "Indicator mapping rules: "
        "- Use 'extra_steps' (ccpa_pattern: 'subscription_trap') when reaching the final cancel screen takes more than 2 clicks. "
        "- Use 'hidden_cancel' (ccpa_pattern: 'interface_interference') when the cancel link is buried in nested menus or styled in tiny/muted text next to a prominent 'Keep plan' button. "
        "- Use 'redirects' (ccpa_pattern: 'subscription_trap' or 'bait_and_switch') for circular menus or dead-end pages. "
        "- Use 'forced_reason' (ccpa_pattern: 'forced_action') when a mandatory reason/survey is required to continue. "
        "- Use 'retention_offer' (ccpa_pattern: 'nagging' or 'false_urgency') when discount or pause offers interrupt the cancellation flow. "
        "- Use 'unclear_copy' (ccpa_pattern: 'confirm_shaming' or 'trick_question') for guilt-tripping copy or confusing button labels. "
        "Return ONLY valid JSON with these exact keys: "
        "{"
        '"blocked": boolean, '
        '"block_reason": string or null, '
        '"stopped_at_button": string or null, '
        '"cancellation_completed": boolean, '
        '"findings": ['
        "  {"
        '    "indicator": one of ["extra_steps","hidden_cancel","redirects","forced_reason","retention_offer","unclear_copy"], '
        '    "title": string, '
        '    "description": string, '
        '    "step_number": integer, '
        '    "step_refs": [integer], '
        '    "evidence_quote": string (exact visible button text, copy, or menu path observed), '
        '    "ccpa_pattern": one of ["subscription_trap","interface_interference","confirm_shaming","nagging","forced_action","false_urgency","trick_question"], '
        '    "ccpa_rationale": string'
        "  }"
        "]"
        "}"
    )


def _contains_unnegated_keyword(text: str) -> str | None:
    lowered = text.lower()
    for phrase in NEGATED_BARRIER_PHRASES:
        lowered = lowered.replace(phrase, "")
    for kw in BLOCK_KEYWORDS:
        if kw in lowered:
            return kw
    return None


def detect_barrier(steps: list[str], result_json: dict[str, Any] | None) -> str | None:
    """Box E: 'Agent complete != verified outcome' & 'CAPTCHA / auth barriers -> stop + report'."""
    if isinstance(result_json, dict):
        if result_json.get("blocked") is True:
            return str(result_json.get("block_reason") or "Blocked by login wall, CAPTCHA, or anti-bot gate.")
        # If the agent explicitly reported blocked=False and produced findings, do not false-positive on descriptions
        has_findings = isinstance(result_json.get("findings"), list) and len(result_json["findings"]) > 0
        if result_json.get("blocked") is False and has_findings:
            return None
        kw = _contains_unnegated_keyword(json.dumps(result_json))
        if kw:
            return f"Target site returned an anti-bot or security barrier matching '{kw}'."

    kw = _contains_unnegated_keyword(" ".join(steps))
    if kw:
        return f"Observed step encountered barrier matching '{kw}'."
    return None


def _is_meta_step(label: str) -> bool:
    lowered = label.strip().lower()
    return any(lowered.startswith(prefix) for prefix in META_STEP_PREFIXES)


def normalise_and_build_report(
    run_id: str,
    service: str,
    steps: list[tuple[int, str, datetime]],
    streaming_url: str | None,
    result_json: dict[str, Any] | None,
    error_message: str | None = None,
) -> Report:
    """Box B & D: Normalise raw observations into Evidence, classify indicators, and compute weighted score."""
    if error_message:
        return Report(
            run_id=run_id,
            service=service,
            outcome="failed",
            friction_score=0,
            safety_gate_stopped=False,
            stop_reason="error",
            streaming_url=streaming_url,
            friction_signals=[],
            evidence=[],
            ccpa_alignment=[],
            limitations=[
                f"Audit failed before completion: {error_message}",
                "No verified friction score could be computed.",
            ],
        )

    step_labels = [label for _, label, _ in steps]
    barrier = detect_barrier(step_labels, result_json)
    if barrier:
        ev_list: list[Evidence] = []
        if steps:
            last_idx, last_label, last_ts = steps[-1]
            ev_list.append(
                Evidence(
                    id="ev_block",
                    step=last_idx,
                    kind="text",
                    timestamp=last_ts,
                    content=f"{barrier} (Last observed step: {last_label})",
                )
            )
        return Report(
            run_id=run_id,
            service=service,
            outcome="human_required",
            friction_score=0,
            safety_gate_stopped=False,
            stop_reason="blocked",
            streaming_url=streaming_url,
            friction_signals=[],
            evidence=ev_list,
            ccpa_alignment=[],
            limitations=[
                f"Barrier detected (Agent complete != verified outcome): {barrier}",
                "Human intervention or an authenticated session is required to continue.",
            ],
        )

    evidence: list[Evidence] = []
    raw_signals: list[FrictionSignal] = []
    ccpa_map: dict[CcpaPattern, list[str]] = {}
    ccpa_rationales: dict[CcpaPattern, list[str]] = {}

    raw_findings = (result_json or {}).get("findings") if isinstance(result_json, dict) else None
    if not isinstance(raw_findings, list):
        raw_findings = []

    step_ts_map = {idx: ts for idx, _, ts in steps}
    ui_step_indices = [idx for idx, lbl, _ in steps if not _is_meta_step(lbl)]
    if not ui_step_indices and steps:
        ui_step_indices = [idx for idx, _, _ in steps]
    effective_total_steps = len(ui_step_indices) if ui_step_indices else len(steps)
    max_step_idx = len(steps) or 1
    default_ts = now()

    for i, item in enumerate(raw_findings, start=1):
        if not isinstance(item, dict):
            continue
        raw_ind = str(item.get("indicator", "unclear_copy"))
        indicator: FrictionIndicator = (
            raw_ind if raw_ind in VALID_INDICATORS else "unclear_copy"  # type: ignore[assignment]
        )
        raw_step_num = int(item.get("step_number") or max_step_idx)
        step_num = min(max(1, raw_step_num), max_step_idx)

        raw_refs = item.get("step_refs")
        if isinstance(raw_refs, list) and raw_refs:
            step_refs = sorted(
                {min(max(1, int(r)), max_step_idx) for r in raw_refs if isinstance(r, (int, float))}
            )
        else:
            step_refs = [step_num]

        if indicator == "extra_steps" and len(step_refs) <= 1 and len(ui_step_indices) > 1:
            step_refs = list(ui_step_indices)

        quote = item.get("evidence_quote")
        ev_ids: list[str] = []

        if isinstance(quote, str) and quote.strip():
            ev_id = f"ev_{len(evidence) + 1}"
            evidence.append(
                Evidence(
                    id=ev_id,
                    step=step_num,
                    kind="text",
                    timestamp=step_ts_map.get(step_num, default_ts),
                    content=quote.strip(),
                )
            )
            ev_ids.append(ev_id)

        sig_id = f"sig_{i}"
        sig_title = str(item.get("title") or f"Observed {indicator.replace('_', ' ')}")
        sig_desc = str(item.get("description") or "Observed during cancellation flow walk.")
        raw_signals.append(
            FrictionSignal(
                id=sig_id,
                indicator=indicator,
                title=sig_title,
                severity=INDICATOR_SEVERITY[indicator],  # type: ignore[arg-type]
                description=sig_desc,
                step_refs=step_refs or [step_num],
                evidence_ids=ev_ids,
            )
        )

        raw_ccpa = str(item.get("ccpa_pattern") or "")
        pattern: CcpaPattern = (
            raw_ccpa if raw_ccpa in VALID_CCPA else INDICATOR_TO_DEFAULT_CCPA[indicator]  # type: ignore[assignment]
        )
        if indicator == "extra_steps":
            pattern = "subscription_trap"
        ccpa_map.setdefault(pattern, []).append(sig_id)
        custom_rationale = str(item.get("ccpa_rationale") or "").strip()
        if custom_rationale:
            ccpa_rationales.setdefault(pattern, []).append(custom_rationale)

    # Auto-detect extra_steps if >2 UI steps were observed and extra_steps was not reported
    if effective_total_steps > 2 and not any(s.indicator == "extra_steps" for s in raw_signals):
        ev_id = f"ev_{len(evidence) + 1}"
        evidence.append(
            Evidence(
                id=ev_id,
                step=ui_step_indices[-1] if ui_step_indices else len(steps),
                kind="text",
                timestamp=steps[-1][2],
                content=f"Cancellation flow required {effective_total_steps} observed steps: "
                + " -> ".join(lbl for idx, lbl, _ in steps if idx in ui_step_indices[:6]),
            )
        )
        sig_id = f"sig_{len(raw_signals) + 1}"
        raw_signals.insert(
            0,
            FrictionSignal(
                id=sig_id,
                indicator="extra_steps",
                title=f"{effective_total_steps} steps required to navigate toward cancellation",
                severity="high",
                description="Flow exceeded the 2-step baseline to reach the cancellation control.",
                step_refs=list(ui_step_indices),
                evidence_ids=[ev_id],
            ),
        )
        ccpa_map.setdefault("subscription_trap", []).insert(0, sig_id)

    total_score, scored_signals = score_signals(
        raw_signals, evidence, total_steps=effective_total_steps if effective_total_steps else None
    )

    # Safety gate evaluation
    cancellation_completed = bool(
        isinstance(result_json, dict) and result_json.get("cancellation_completed") is True
    )
    stopped_at = (
        result_json.get("stopped_at_button") if isinstance(result_json, dict) else None
    )
    safety_gate_stopped = not cancellation_completed

    # Outcome classification (Box E)
    if not scored_signals:
        outcome: AuditOutcome = "unverified"
    elif all(s.verified for s in scored_signals):
        outcome = "completed_with_evidence"
    elif any(s.verified for s in scored_signals):
        outcome = "partial_evidence"
    else:
        outcome = "unverified"

    ccpa_alignment = [
        CcpaAlignment(
            pattern=pat,
            signal_ids=sig_ids,
            rationale=(
                ccpa_rationales[pat][0]
                if pat in ccpa_rationales and ccpa_rationales[pat]
                else CCPA_DEFAULT_RATIONALES.get(
                    pat,
                    f"Candidate CCPA '{pat.replace('_', ' ')}' signal linked to {', '.join(sig_ids)}.",
                )
            ),
        )
        for pat, sig_ids in ccpa_map.items()
    ]

    limitations = [
        f"Safety gate stopped before final cancellation button ({stopped_at or 'pre-cancellation boundary'})."
        if safety_gate_stopped
        else "WARNING: Agent output did not confirm stopping before final cancellation.",
    ]
    unverified_count = sum(1 for s in scored_signals if not s.verified)
    if unverified_count:
        limitations.append(
            f"{unverified_count} finding(s) lacked captured evidence and were marked unverified (0 points added)."
        )

    return Report(
        run_id=run_id,
        service=service,
        outcome=outcome,
        friction_score=total_score,
        safety_gate_stopped=safety_gate_stopped,
        stop_reason="pre_cancellation_boundary" if safety_gate_stopped else "error",
        streaming_url=streaming_url,
        friction_signals=scored_signals,
        evidence=evidence,
        ccpa_alignment=ccpa_alignment,
        limitations=limitations,
    )


async def stream_audit_run(
    run_id: str,
    run_state: dict[str, Any],
    mock_delay_seconds: float = 0.6,
) -> AsyncIterator[RunEvent]:
    """Stream SSE RunEvents for a run (real TinyFish if start_url + API key present, else mock fallback)."""
    # If already finished, replay cached events so page refreshes never re-trigger TinyFish
    if run_state.get("events"):
        for ev in run_state["events"]:
            yield ev
        return

    raw_start_url: str | None = run_state.get("start_url")
    service: str = run_state["service"]
    start_url: str | None = resolve_effective_start_url(service, raw_start_url)
    api_key = os.getenv("TINYFISH_API_KEY")

    # Demo fallback path (when no real external start_url or no API key is configured)
    if not should_use_live_tinyfish(raw_start_url, service):
        demo_steps = mock_steps_for_run(service, start_url)
        recorded_events: list[RunEvent] = []
        for i, label in enumerate(demo_steps, start=1):
            ev = mock_step_event(i, label)
            recorded_events.append(ev)
            yield ev
            if mock_delay_seconds > 0:
                await asyncio.sleep(mock_delay_seconds)

        report = mock_report(run_id, service, start_url)
        last = len(demo_steps)
        stopped_ev = RunEvent(
            type="stopped",
            step=last,
            label=(
                "Stopped before the final cancellation action"
                if report.stop_reason == "pre_cancellation_boundary"
                else f"Audit stopped ({report.stop_reason})"
            ),
            timestamp=now(),
            stop_reason=report.stop_reason,
        )
        ready_ev = RunEvent(
            type="report_ready",
            step=last,
            label="Report ready",
            timestamp=now(),
        )
        recorded_events.extend([stopped_ev, ready_ev])
        run_state["events"] = recorded_events
        run_state["report"] = report
        yield stopped_ev
        yield ready_ev
        return

    # Real TinyFish execution bridged from a worker thread via asyncio.Queue
    from tinyfish import CompleteEvent, ProgressEvent, StreamingUrlEvent, TinyFish

    queue: asyncio.Queue[RunEvent | None] = asyncio.Queue()
    loop = asyncio.get_running_loop()
    observed_steps: list[tuple[int, str, datetime]] = []
    recorded_events = []
    streaming_url: str | None = None
    result_json: dict[str, Any] | None = None
    error_message: str | None = None

    def worker() -> None:
        nonlocal streaming_url, result_json, error_message
        try:
            client = TinyFish(api_key=api_key)
            goal = build_audit_goal(service)
            with client.agent.stream(url=start_url, goal=goal) as stream:
                for event in stream:
                    ts = now()
                    if isinstance(event, StreamingUrlEvent):
                        streaming_url = event.streaming_url
                    elif isinstance(event, ProgressEvent):
                        step_no = len(observed_steps) + 1
                        observed_steps.append((step_no, event.purpose, ts))
                        run_ev = RunEvent(
                            type="step",
                            step=step_no,
                            label=event.purpose,
                            timestamp=ts,
                            streaming_url=streaming_url,
                        )
                        loop.call_soon_threadsafe(queue.put_nowait, run_ev)
                    elif isinstance(event, CompleteEvent):
                        if event.error:
                            error_message = str(event.error)
                        if isinstance(event.result_json, dict):
                            result_json = event.result_json
        except Exception as exc:  # noqa: BLE001
            error_message = str(exc)
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    worker_future = loop.run_in_executor(None, worker)

    while True:
        item = await queue.get()
        if item is None:
            break
        recorded_events.append(item)
        yield item

    await worker_future

    report = normalise_and_build_report(
        run_id=run_id,
        service=service,
        steps=observed_steps,
        streaming_url=streaming_url,
        result_json=result_json,
        error_message=error_message,
    )
    run_state["report"] = report

    last_step = len(observed_steps)
    stopped_ev = RunEvent(
        type="stopped" if report.stop_reason != "error" else "error",
        step=last_step,
        label=(
            "Stopped before the final cancellation action"
            if report.stop_reason == "pre_cancellation_boundary"
            else f"Audit stopped ({report.stop_reason})"
        ),
        timestamp=now(),
        streaming_url=streaming_url,
        stop_reason=report.stop_reason,
    )
    ready_ev = RunEvent(
        type="report_ready",
        step=last_step,
        label="Report ready",
        timestamp=now(),
        streaming_url=streaming_url,
    )
    recorded_events.extend([stopped_ev, ready_ev])
    run_state["events"] = recorded_events
    yield stopped_ev
    yield ready_ev
