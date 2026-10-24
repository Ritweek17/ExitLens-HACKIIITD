"""Audit Orchestrator, TinyFish Adapter, Evidence Normaliser & Safety Gate (Boxes B, D, E)."""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, AsyncIterator
from urllib.parse import urlparse

from mock_data import MOCK_STEPS, mock_report, mock_step_event, now
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
)

# Documentation placeholder/local hosts default to the fast deterministic mock path
DEMO_FALLBACK_HOSTS = {"example.in", "www.example.in", "example.com", "www.example.com", "localhost", "127.0.0.1"}


def should_use_live_tinyfish(start_url: str | None) -> bool:
    """Return True only when a real external target URL and TINYFISH_API_KEY are present."""
    if not start_url or not os.getenv("TINYFISH_API_KEY"):
        return False
    host = (urlparse(start_url).hostname or "").lower()
    return bool(host) and host not in DEMO_FALLBACK_HOSTS


def build_audit_goal(service: str) -> str:
    return (
        f"You are auditing the subscription cancellation journey for '{service}' in India. "
        "Navigate toward cancelling the subscription and observe every step, dark pattern, or barrier. "
        "CRITICAL SAFETY RULE: STOP BEFORE clicking any final 'Cancel subscription' or 'Confirm cancellation' button. "
        "Never complete an irreversible cancellation. "
        "If you hit a CAPTCHA, Cloudflare block, or login wall that you cannot pass, stop immediately and report it. "
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
        '    "evidence_quote": string or null, '
        '    "ccpa_pattern": one of ["subscription_trap","interface_interference","confirm_shaming","nagging","forced_action","false_urgency","trick_question"]'
        "  }"
        "]"
        "}"
    )


def detect_barrier(steps: list[str], result_json: dict[str, Any] | None) -> str | None:
    """Box E: 'Agent complete != verified outcome' & 'CAPTCHA / auth barriers -> stop + report'."""
    if isinstance(result_json, dict):
        if result_json.get("blocked") is True:
            return str(result_json.get("block_reason") or "Blocked by login wall, CAPTCHA, or anti-bot gate.")
        serialized = json.dumps(result_json).lower()
        for kw in BLOCK_KEYWORDS:
            if kw in serialized:
                return f"Target site returned an anti-bot or security barrier matching '{kw}'."

    joined_steps = " ".join(steps).lower()
    for kw in BLOCK_KEYWORDS:
        if kw in joined_steps:
            return f"Observed step encountered barrier matching '{kw}'."
    return None


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

    raw_findings = (result_json or {}).get("findings") if isinstance(result_json, dict) else None
    if not isinstance(raw_findings, list):
        raw_findings = []

    step_ts_map = {idx: ts for idx, _, ts in steps}
    default_ts = now()

    for i, item in enumerate(raw_findings, start=1):
        if not isinstance(item, dict):
            continue
        raw_ind = str(item.get("indicator", "unclear_copy"))
        indicator: FrictionIndicator = (
            raw_ind if raw_ind in VALID_INDICATORS else "unclear_copy"  # type: ignore[assignment]
        )
        step_num = int(item.get("step_number") or (len(steps) or 1))
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
        raw_signals.append(
            FrictionSignal(
                id=sig_id,
                indicator=indicator,
                title=str(item.get("title") or f"Observed {indicator.replace('_', ' ')}"),
                severity=INDICATOR_SEVERITY[indicator],  # type: ignore[arg-type]
                description=str(item.get("description") or "Observed during cancellation flow walk."),
                step_refs=[step_num],
                evidence_ids=ev_ids,
            )
        )

        raw_ccpa = str(item.get("ccpa_pattern") or "")
        pattern: CcpaPattern = (
            raw_ccpa if raw_ccpa in VALID_CCPA else INDICATOR_TO_DEFAULT_CCPA[indicator]  # type: ignore[assignment]
        )
        ccpa_map.setdefault(pattern, []).append(sig_id)

    # Auto-detect extra_steps if >2 steps were observed and extra_steps was not reported
    if len(steps) > 2 and not any(s.indicator == "extra_steps" for s in raw_signals):
        ev_id = f"ev_{len(evidence) + 1}"
        evidence.append(
            Evidence(
                id=ev_id,
                step=len(steps),
                kind="text",
                timestamp=steps[-1][2],
                content=f"Cancellation flow required {len(steps)} observed steps: "
                + " -> ".join(lbl for _, lbl, _ in steps[:6]),
            )
        )
        sig_id = f"sig_{len(raw_signals) + 1}"
        raw_signals.insert(
            0,
            FrictionSignal(
                id=sig_id,
                indicator="extra_steps",
                title=f"{len(steps)} steps required to navigate toward cancellation",
                severity="high",
                description="Flow exceeded the 2-step baseline to reach the cancellation control.",
                step_refs=[idx for idx, _, _ in steps],
                evidence_ids=[ev_id],
            ),
        )
        ccpa_map.setdefault("subscription_trap", []).append(sig_id)

    total_score, scored_signals = score_signals(
        raw_signals, evidence, total_steps=len(steps) if steps else None
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
            rationale=f"Candidate CCPA '{pat.replace('_', ' ')}' signal linked to {', '.join(sig_ids)}.",
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

    start_url: str | None = run_state.get("start_url")
    service: str = run_state["service"]
    api_key = os.getenv("TINYFISH_API_KEY")

    # Demo fallback path (when no real external start_url or no API key is configured)
    if not should_use_live_tinyfish(start_url):
        recorded_events: list[RunEvent] = []
        for i, label in enumerate(MOCK_STEPS, start=1):
            ev = mock_step_event(i, label)
            recorded_events.append(ev)
            yield ev
            if mock_delay_seconds > 0:
                await asyncio.sleep(mock_delay_seconds)

        last = len(MOCK_STEPS)
        stopped_ev = RunEvent(
            type="stopped",
            step=last,
            label="Stopped before the final cancellation action",
            timestamp=now(),
            stop_reason="pre_cancellation_boundary",
        )
        ready_ev = RunEvent(
            type="report_ready",
            step=last,
            label="Report ready",
            timestamp=now(),
        )
        recorded_events.extend([stopped_ev, ready_ev])
        run_state["events"] = recorded_events
        run_state["report"] = mock_report(run_id, service)
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
