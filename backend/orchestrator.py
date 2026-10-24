"""Audit Orchestrator, TinyFish Adapter, Evidence Normaliser & Safety Gate (Boxes B, D, E)."""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, AsyncIterator
from urllib.parse import urlparse

from mock_data import (
    PRESETS,
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
from test_accounts import TestAccountRecord, verify_dedicated_test_account

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

# Phrases in TinyFish error text that indicate a genuine anti-bot / auth barrier. Deliberately
# specific: generic words ("bot", "login", "timeout", bare status codes) also appear in ordinary
# failures and must not turn a plain error into a `human_required` barrier report.
ERROR_BARRIER_KEYWORDS = (
    "error 1200",
    "cloudflare",
    "captcha",
    "verify you are human",
    "access denied",
    "err_access_denied",
    "err_http2_protocol_error",
    "attention required",
    "bot detection",
    "blocked by automated browser",
    "login required",
    "login-gated",
    "sign in to continue",
    "authentication required",
    "unauthorized",
    "forbidden",
)

INFRA_ERROR_KEYWORDS = (
    "invalid api key",
    "authenticationerror",
    "billing_failure",
    "paymentrequired",
    "ratelimit",
    "quota",
    "insufficient",
)

TUNNEL_HOST_SUFFIXES = (
    ".lhr.life",
    ".ngrok-free.app",
    ".ngrok.io",
    ".trycloudflare.com",
    ".loca.lt",
)

AUDIT_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "blocked": {"type": "boolean"},
        "block_reason": {"type": "string", "nullable": True},
        "account_mismatch": {"type": "boolean"},
        "stopped_at_button": {"type": "string", "nullable": True},
        "cancellation_completed": {"type": "boolean"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "indicator": {
                        "type": "string",
                        "enum": [
                            "extra_steps",
                            "hidden_cancel",
                            "redirects",
                            "forced_reason",
                            "retention_offer",
                            "unclear_copy",
                        ],
                    },
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "step_number": {"type": "integer"},
                    "step_refs": {"type": "array", "items": {"type": "integer"}},
                    "evidence_quote": {"type": "string", "nullable": True},
                    "ccpa_pattern": {
                        "type": "string",
                        "enum": [
                            "subscription_trap",
                            "interface_interference",
                            "confirm_shaming",
                            "nagging",
                            "forced_action",
                            "false_urgency",
                            "trick_question",
                        ],
                    },
                    "ccpa_rationale": {"type": "string", "nullable": True},
                },
                "required": [
                    "indicator",
                    "title",
                    "description",
                    "step_number",
                    "evidence_quote",
                    "ccpa_pattern",
                ],
            },
        },
    },
    "required": [
        "blocked",
        "block_reason",
        "stopped_at_button",
        "cancellation_completed",
        "findings",
    ],
}

NEGATED_BARRIER_PHRASES = (
    "no captcha",
    "no cloudflare",
    "without captcha",
    "without cloudflare",
    "no login wall",
    "not blocked",
)

META_STEP_PREFIXES = (
    "submit ",
    "present ",
    "extract ",
    "get full",
    "get detailed",
    "capture ",
    "understand ",
    "visual inspection",
    "check context",
    "document the",
    "report blocked",
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


DEFAULT_RUN_TIME_LIMIT_SECONDS = 300.0


def get_run_time_limit_seconds() -> float:
    """Overall wall-clock limit for one live TinyFish run (env `TINYFISH_RUN_TIMEOUT_SECONDS`)."""
    raw = (os.getenv("TINYFISH_RUN_TIMEOUT_SECONDS") or "").strip()
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_RUN_TIME_LIMIT_SECONDS
    return value if value > 0 else DEFAULT_RUN_TIME_LIMIT_SECONDS


def get_allowed_audit_hosts() -> set[str]:
    """Hosts from the optional `ALLOWED_AUDIT_HOSTS` env var (comma-separated). Empty = no restriction."""
    raw = os.getenv("ALLOWED_AUDIT_HOSTS") or ""
    return {h.strip().lower().lstrip("*.").lstrip(".") for h in raw.split(",") if h.strip()}


def is_start_url_allowed(start_url: str | None) -> bool:
    """Server-side guard for live audit targets.

    With no allowlist configured every URL is allowed (the human approval flags still apply).
    When `ALLOWED_AUDIT_HOSTS` is set, only these hosts (and their subdomains) may be audited:
    the configured hosts, the curated preset hosts, local/demo fallback hosts, tunnel hosts and
    the host of `PUBLIC_DEMO_BASE_URL`.
    """
    allowed = get_allowed_audit_hosts()
    if not allowed or not start_url:
        return True
    host = (urlparse(start_url).hostname or "").lower()
    if not host:
        return False
    allowed |= DEMO_FALLBACK_HOSTS
    for preset in PRESETS:
        if preset.default_start_url:
            allowed.add((urlparse(str(preset.default_start_url)).hostname or "").lower())
    public_host = (urlparse(os.getenv("PUBLIC_DEMO_BASE_URL") or "").hostname or "").lower()
    if public_host:
        allowed.add(public_host)
    if is_tunnel_demo_url(start_url):
        return True
    allowed.discard("")
    return any(host == a or host.endswith("." + a) for a in allowed)


def should_use_live_tinyfish(start_url: str | None, service: str = "") -> bool:
    """Return True only when a real external target URL (or PUBLIC_DEMO_BASE_URL) and TINYFISH_API_KEY are present."""
    effective_url = resolve_effective_start_url(service, start_url)
    if not effective_url or not os.getenv("TINYFISH_API_KEY"):
        return False
    host = (urlparse(effective_url).hostname or "").lower()
    return bool(host) and host not in DEMO_FALLBACK_HOSTS


def build_audit_goal(service: str, test_account: TestAccountRecord | None = None) -> str:
    account_clause = ""
    if test_account is not None:
        account_clause = (
            f"DEDICATED TEST ACCOUNT GATE: This run is bound to dedicated test account "
            f"'{test_account.masked_identifier}' ({test_account.id}). If the page displays a logged-in "
            "account email or username that clearly belongs to a different personal account, "
            "STOP IMMEDIATELY and return blocked=true, account_mismatch=true, and "
            "block_reason='Account identity mismatch with approved dedicated test account'. "
        )
    return (
        f"You are auditing the subscription cancellation journey for '{service}' in India. "
        "Navigate toward cancelling the subscription and observe every step, dark pattern, or barrier. "
        "CRITICAL SAFETY RULE: STOP BEFORE clicking any final 'Cancel subscription' or 'Confirm cancellation' button. "
        "Never complete an irreversible cancellation. "
        + account_clause
        + "NAVIGATION DISCIPLINE & ACTION BUDGET (MAX 15 ACTIONS): "
        "1. If you hit a CAPTCHA, Cloudflare block, OTP gate, or login/sign-in page that you cannot pass with an already-authenticated session, STOP IMMEDIATELY and return blocked=true with a clear block_reason. "
        "2. Never attempt to navigate to a membership/cancellation URL or click a 'Cancel Now' / 'Manage subscription' link more than ONCE. If the first attempt fails to load, stays on the support article, or lands on a logged-out page (such as a page with a 'Sign in' button or a marketing/signup page with no active plan), STOP IMMEDIATELY and return blocked=true explaining that authentication is required. "
        "3. Do NOT loop back to help/support articles, retry URL parameters, or repeatedly extract instructions once you see that the cancellation page requires login. "
        "4. Do NOT waste actions changing country/region dropdowns, language selectors, or expanding unrelated troubleshooting/FAQ accordions. "
        "If the cancellation flow is fair, transparent, and direct (1-2 clicks with equal visual button styling and no dark patterns), return an empty findings array (\"findings\": []). Do not invent friction on a clean exit flow. "
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


def is_tunnel_demo_url(url: str | None) -> bool:
    if not url:
        return False
    host = (urlparse(url).hostname or "").lower()
    return any(host.endswith(suffix) for suffix in TUNNEL_HOST_SUFFIXES)


def build_tinyfish_stream_kwargs(
    start_url: str,
    goal: str,
    test_account: TestAccountRecord | None = None,
) -> dict[str, Any]:
    """Build TinyFish `agent.stream()` kwargs with stealth profile, optional India proxy, and JSON schema."""
    from tinyfish import BrowserProfile, ProxyConfig

    is_tunnel = is_tunnel_demo_url(start_url)
    env_profile = (os.getenv("TINYFISH_BROWSER_PROFILE") or "").strip().lower()
    if env_profile == "lite":
        profile = BrowserProfile.LITE
    elif env_profile == "stealth":
        profile = BrowserProfile.STEALTH
    else:
        profile = BrowserProfile.LITE if is_tunnel else BrowserProfile.STEALTH

    kwargs: dict[str, Any] = {
        "url": start_url,
        "goal": goal,
        "browser_profile": profile,
        "output_schema": AUDIT_OUTPUT_SCHEMA,
    }

    proxy_country = (os.getenv("TINYFISH_PROXY_COUNTRY") or "").strip().upper()
    if proxy_country and not is_tunnel:
        kwargs["proxy_config"] = ProxyConfig(enabled=True, country_code=proxy_country)

    if not is_tunnel:
        acct_profile_id = test_account.profile_id if test_account else None
        profile_id = acct_profile_id or (os.getenv("TINYFISH_PROFILE_ID") or "").strip()
        if profile_id:
            kwargs["use_profile"] = True
            kwargs["profile_id"] = profile_id

        use_vault_env = (os.getenv("TINYFISH_USE_VAULT") or "").strip().lower()
        acct_creds = list(test_account.credential_item_ids) if test_account else []
        cred_ids_raw = (os.getenv("TINYFISH_CREDENTIAL_ITEM_IDS") or "").strip()
        cred_ids = acct_creds or [c.strip() for c in cred_ids_raw.split(",") if c.strip()]
        if use_vault_env in ("1", "true", "yes") or cred_ids:
            kwargs["use_vault"] = True
            if cred_ids:
                kwargs["credential_item_ids"] = cred_ids

    return kwargs


def format_tinyfish_error(err: Any) -> str:
    if err is None:
        return ""
    msg = getattr(err, "message", None)
    cat = getattr(err, "category", None)
    code = getattr(err, "code", None)
    if msg:
        prefix = str(code or cat or "ERROR")
        return f"[{prefix}] {msg}"
    text = str(err)
    if "validation error for CompleteEvent" in text and "input_value=" in text:
        return "Target URL or login-gated page was blocked by automated browser policy."
    return text


def _contains_unnegated_keyword(text: str) -> str | None:
    lowered = text.lower()
    for phrase in NEGATED_BARRIER_PHRASES:
        lowered = lowered.replace(phrase, "")
    for kw in BLOCK_KEYWORDS:
        if kw in lowered:
            return kw
    return None


def detect_barrier(
    steps: list[str],
    result_json: dict[str, Any] | None,
    error_message: str | None = None,
) -> str | None:
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

    if error_message:
        err_lower = error_message.lower()
        if not any(infra in err_lower for infra in INFRA_ERROR_KEYWORDS):
            for bkw in ERROR_BARRIER_KEYWORDS:
                if bkw in err_lower:
                    return f"Target site blocked automated browser or requires human authentication ({error_message})."
    return None


def _safe_int(value: Any, default: int | None) -> int | None:
    """Parse agent-provided numbers defensively; bools and non-numeric values yield `default`."""
    if isinstance(value, bool):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


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
    test_account_ref: str | None = None,
    stop_override: StopReason | None = None,
) -> Report:
    """Box B & D: Normalise raw observations into Evidence, classify indicators, and compute weighted score."""
    if (
        isinstance(result_json, dict) and result_json.get("account_mismatch") is True
    ) or stop_override == "account_verification_failed":
        reason_str = (
            str(result_json.get("block_reason") or "")
            if isinstance(result_json, dict)
            else ""
        ) or "Dedicated test account verification failed: logged-in identity did not match the approved test account."
        last_idx, last_ts = (steps[-1][0], steps[-1][2]) if steps else (0, now())
        return Report(
            run_id=run_id,
            service=service,
            outcome="unverified",
            friction_score=0,
            safety_gate_stopped=False,
            stop_reason="account_verification_failed",
            test_account_ref=test_account_ref,
            account_verified=False,
            streaming_url=streaming_url,
            friction_signals=[],
            evidence=[
                Evidence(
                    id="ev_acct",
                    step=last_idx,
                    kind="text",
                    timestamp=last_ts,
                    content=reason_str,
                )
            ],
            ccpa_alignment=[],
            limitations=[
                reason_str,
                "Audit stopped immediately because only verified dedicated test accounts may be audited.",
            ],
        )

    if stop_override is not None and stop_override != "error":
        partial_ev = [
            Evidence(
                id=f"ev_{i}",
                step=step_idx,
                kind="text",
                timestamp=step_ts,
                content=f"Observed step {step_idx}: {step_label}",
            )
            for i, (step_idx, step_label, step_ts) in enumerate(steps, start=1)
        ]
        return Report(
            run_id=run_id,
            service=service,
            outcome="partial_evidence" if steps else "unverified",
            friction_score=0,
            safety_gate_stopped=True,
            stop_reason=stop_override,
            test_account_ref=test_account_ref,
            account_verified=True,
            streaming_url=streaming_url,
            friction_signals=[],
            evidence=partial_ev,
            ccpa_alignment=[],
            limitations=[
                f"Audit stopped manually before completion ({stop_override}).",
                f"Preserved {len(steps)} observed step(s) recorded prior to stopping.",
            ],
        )

    step_labels = [label for _, label, _ in steps]
    barrier = detect_barrier(step_labels, result_json, error_message)
    if barrier:
        if steps:
            last_idx, last_label, last_ts = steps[-1]
            ev_content = f"{barrier} (Last observed step: {last_label})"
        else:
            last_idx, last_ts = 0, now()
            ev_content = barrier
        ev_list = [
            Evidence(
                id="ev_block",
                step=last_idx,
                kind="text",
                timestamp=last_ts,
                content=ev_content,
            )
        ]
        return Report(
            run_id=run_id,
            service=service,
            outcome="human_required",
            friction_score=0,
            safety_gate_stopped=False,
            stop_reason="blocked",
            test_account_ref=test_account_ref,
            account_verified=True,
            streaming_url=streaming_url,
            friction_signals=[],
            evidence=ev_list,
            ccpa_alignment=[],
            limitations=[
                f"Barrier detected (Agent complete != verified outcome): {barrier}",
                "Human intervention or an authenticated session is required to continue.",
            ],
        )

    if error_message:
        if steps:
            partial_ev = [
                Evidence(
                    id=f"ev_{i}",
                    step=step_idx,
                    kind="text",
                    timestamp=step_ts,
                    content=f"Observed step {step_idx}: {step_label}",
                )
                for i, (step_idx, step_label, step_ts) in enumerate(steps, start=1)
            ]
            return Report(
                run_id=run_id,
                service=service,
                outcome="partial_evidence",
                friction_score=0,
                safety_gate_stopped=False,
                stop_reason="error",
                test_account_ref=test_account_ref,
                account_verified=True,
                streaming_url=streaming_url,
                friction_signals=[],
                evidence=partial_ev,
                ccpa_alignment=[],
                limitations=[
                    f"Audit interrupted before completion: {error_message}",
                    f"Partial evidence preserved from {len(steps)} observed step(s) prior to interruption; no verified friction score could be computed.",
                ],
            )
        return Report(
            run_id=run_id,
            service=service,
            outcome="failed",
            friction_score=0,
            safety_gate_stopped=False,
            stop_reason="error",
            test_account_ref=test_account_ref,
            account_verified=True,
            streaming_url=streaming_url,
            friction_signals=[],
            evidence=[],
            ccpa_alignment=[],
            limitations=[
                f"Audit failed before completion: {error_message}",
                "No verified friction score could be computed.",
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
        # Do not allow a false-positive extra_steps signal when UI steps are within the 2-step baseline
        if indicator == "extra_steps" and steps and effective_total_steps <= 2:
            continue
        raw_step_num = _safe_int(item.get("step_number"), max_step_idx)
        step_num = min(max(1, raw_step_num), max_step_idx)

        raw_refs = item.get("step_refs")
        step_refs = []
        if isinstance(raw_refs, list):
            parsed_refs = (_safe_int(r, None) for r in raw_refs)
            step_refs = sorted({min(max(1, r), max_step_idx) for r in parsed_refs if r is not None})
        if not step_refs:
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
        if safety_gate_stopped and isinstance(result_json, dict) and (stopped_at or steps):
            outcome: AuditOutcome = "completed_with_evidence"
            if not evidence and steps:
                evidence.append(
                    Evidence(
                        id="ev_1",
                        step=ui_step_indices[-1] if ui_step_indices else len(steps),
                        kind="text",
                        timestamp=steps[-1][2],
                        content=(
                            f"Direct {effective_total_steps}-step exit path verified with no dark patterns; "
                            f"stopped at '{stopped_at or 'pre-cancellation boundary'}'."
                        ),
                    )
                )
        else:
            outcome = "unverified"
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
        test_account_ref=test_account_ref,
        account_verified=True,
        streaming_url=streaming_url,
        friction_signals=scored_signals,
        evidence=evidence,
        ccpa_alignment=ccpa_alignment,
        limitations=limitations,
    )


def stop_audit_run(
    run_id: str,
    run_state: dict[str, Any],
    reason: StopReason = "user_stopped",
) -> StopReason:
    """Stop an active or idle audit run and ensure its report reflects the stop reason."""
    if run_state.get("done") and run_state.get("report") is not None:
        return run_state["report"].stop_reason

    run_state["stop_requested"] = reason

    # If the run has not started its background driver yet, finalize it immediately.
    if "task" not in run_state:
        test_account_ref: str | None = run_state.get("test_account_ref")
        report = normalise_and_build_report(
            run_id=run_id,
            service=run_state["service"],
            steps=[],
            streaming_url=None,
            result_json=None,
            test_account_ref=test_account_ref,
            stop_override=reason,
        )
        stopped_ev = RunEvent(
            type="stopped" if reason != "error" else "error",
            step=0,
            label=f"Audit stopped ({reason})",
            timestamp=now(),
            stop_reason=reason if reason != "error" else None,
        )
        events = [stopped_ev]
        if reason != "error":
            events.append(RunEvent(type="report_ready", step=0, label="Report ready", timestamp=now()))
        run_state["buffer"] = list(events)
        run_state["events"] = list(events)
        run_state["report"] = report
        run_state["done"] = True
    return reason


async def stream_audit_run(
    run_id: str,
    run_state: dict[str, Any],
    mock_delay_seconds: float = 0.6,
) -> AsyncIterator[RunEvent]:
    """Stream SSE RunEvents for a run, executing the audit at most once per run.

    The audit runs in a background task that appends events to a shared buffer. Every
    subscriber (first connection, reconnect, duplicate EventSource, page refresh) reads that
    buffer, so a client disconnecting never cancels the run and never triggers a second one.
    """
    buffer: list[RunEvent] = run_state.setdefault("buffer", [])

    # Finished run: replay the buffer without touching any event-loop primitives.
    if run_state.get("done"):
        for ev in buffer:
            yield ev
        return

    if "task" not in run_state:
        run_state["cond"] = asyncio.Condition()
        run_state["task"] = asyncio.create_task(_drive_audit(run_id, run_state, mock_delay_seconds))

    cond: asyncio.Condition = run_state["cond"]
    index = 0
    while True:
        async with cond:
            await cond.wait_for(lambda: index < len(buffer) or run_state.get("done", False))
        while index < len(buffer):
            yield buffer[index]
            index += 1
        if run_state.get("done", False):
            return


async def _drive_audit(
    run_id: str,
    run_state: dict[str, Any],
    mock_delay_seconds: float,
) -> None:
    """Background driver: pump `_produce_audit_events` into the shared buffer exactly once."""
    buffer: list[RunEvent] = run_state["buffer"]
    cond: asyncio.Condition = run_state["cond"]
    try:
        async for ev in _produce_audit_events(run_id, run_state, mock_delay_seconds):
            buffer.append(ev)
            async with cond:
                cond.notify_all()
    except Exception as exc:  # noqa: BLE001 - always end the stream with a terminal event
        if run_state.get("report") is None:
            run_state["report"] = normalise_and_build_report(
                run_id=run_id,
                service=run_state["service"],
                steps=[],
                streaming_url=None,
                result_json=None,
                error_message=f"Audit failed unexpectedly: {exc}",
            )
        buffer.append(
            RunEvent(
                type="error",
                step=len([e for e in buffer if e.type == "step"]),
                label=f"Audit failed: {exc}",
                timestamp=now(),
            )
        )
    finally:
        run_state["done"] = True
        async with cond:
            cond.notify_all()


async def _produce_audit_events(
    run_id: str,
    run_state: dict[str, Any],
    mock_delay_seconds: float = 0.6,
) -> AsyncIterator[RunEvent]:
    """Generate RunEvents (real TinyFish if start_url + API key present, else mock fallback)."""
    raw_start_url: str | None = run_state.get("start_url")
    service: str = run_state["service"]
    test_account_ref: str | None = run_state.get("test_account_ref")
    test_account = verify_dedicated_test_account(test_account_ref) if test_account_ref else None
    start_url: str | None = resolve_effective_start_url(service, raw_start_url)
    api_key = os.getenv("TINYFISH_API_KEY")

    # Demo fallback path (when no real external start_url or no API key is configured)
    if not should_use_live_tinyfish(raw_start_url, service):
        demo_steps = mock_steps_for_run(service, start_url)
        recorded_events: list[RunEvent] = []
        observed_demo: list[tuple[int, str, datetime]] = []
        for i, label in enumerate(demo_steps, start=1):
            if run_state.get("stop_requested"):
                break
            ev = mock_step_event(i, label)
            observed_demo.append((i, label, ev.timestamp))
            recorded_events.append(ev)
            yield ev
            if mock_delay_seconds > 0:
                await asyncio.sleep(mock_delay_seconds)

        stop_req: StopReason | None = run_state.get("stop_requested")
        if stop_req:
            report = normalise_and_build_report(
                run_id=run_id,
                service=service,
                steps=observed_demo,
                streaming_url=None,
                result_json=None,
                test_account_ref=test_account_ref,
                stop_override=stop_req,
            )
            last = len(observed_demo)
        else:
            report = mock_report(run_id, service, start_url, test_account_ref=test_account_ref)
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
            goal = build_audit_goal(service, test_account=test_account)
            stream_kwargs = build_tinyfish_stream_kwargs(start_url or "", goal, test_account=test_account)
            with client.agent.stream(**stream_kwargs) as stream:
                for event in stream:
                    if run_state.get("stop_requested"):
                        break
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
                            error_message = format_tinyfish_error(event.error)
                        if isinstance(event.result_json, dict):
                            result_json = event.result_json
        except Exception as exc:  # noqa: BLE001
            error_message = format_tinyfish_error(exc)
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    worker_future = loop.run_in_executor(None, worker)

    time_limit = get_run_time_limit_seconds()
    deadline = loop.time() + time_limit
    timed_out = False
    while True:
        if run_state.get("stop_requested"):
            break
        remaining = deadline - loop.time()
        if remaining <= 0:
            timed_out = True
            break
        try:
            item = await asyncio.wait_for(queue.get(), timeout=min(0.25, remaining))
        except asyncio.TimeoutError:
            if loop.time() >= deadline:
                timed_out = True
                break
            continue
        if item is None:
            break
        recorded_events.append(item)
        yield item

    stop_override: StopReason | None = run_state.get("stop_requested")
    if stop_override:
        final_error = None
    elif timed_out:
        # The SDK worker thread cannot be cancelled; stop waiting for it and report from a snapshot.
        final_error = f"Audit exceeded the {time_limit:g}s time limit and was stopped."
    else:
        await worker_future
        final_error = error_message
    final_steps = list(observed_steps)
    final_result = None if (timed_out or stop_override) else result_json
    final_streaming_url = streaming_url

    try:
        report = normalise_and_build_report(
            run_id=run_id,
            service=service,
            steps=final_steps,
            streaming_url=final_streaming_url,
            result_json=final_result,
            error_message=final_error,
            test_account_ref=test_account_ref,
            stop_override=stop_override,
        )
    except Exception as exc:  # noqa: BLE001 - never leave the SSE stream without a terminal event
        report = normalise_and_build_report(
            run_id=run_id,
            service=service,
            steps=final_steps,
            streaming_url=final_streaming_url,
            result_json=None,
            error_message=f"Could not process agent output: {exc}",
            test_account_ref=test_account_ref,
        )
    run_state["report"] = report

    last_step = len(final_steps)
    if report.stop_reason == "error":
        # Contract: on failure a single terminal `error` event is sent instead of
        # `stopped` + `report_ready`; the failed report stays fetchable via GET /report.
        error_ev = RunEvent(
            type="error",
            step=last_step,
            label=report.limitations[0] if report.limitations else "Audit failed",
            timestamp=now(),
            streaming_url=final_streaming_url,
        )
        recorded_events.append(error_ev)
        run_state["events"] = recorded_events
        yield error_ev
        return

    stopped_ev = RunEvent(
        type="stopped",
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
