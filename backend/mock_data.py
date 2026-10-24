"""Mock run data & demo fallback path (Box E: 'Demo fallback: mock evidence path')."""

from datetime import datetime, timezone

from models import CcpaAlignment, Evidence, FrictionSignal, Report, RunEvent
from scoring import score_signals

MOCK_STEPS = [
    "Opened account page",
    "Clicked 'Settings'",
    "Clicked 'Membership & billing'",
    "Clicked 'Manage plan'",
    "Dismissed retention offer '50% off for 3 months'",
    "Reached 'Are you sure?' confirm-shaming dialog",
    "Found final 'Confirm cancellation' button - stopped (safety gate)",
]


def now() -> datetime:
    return datetime.now(timezone.utc)


def mock_step_event(step: int, label: str) -> RunEvent:
    return RunEvent(type="step", step=step, label=label, timestamp=now())


def mock_report(run_id: str, service: str) -> Report:
    ts = now()
    evidence = [
        Evidence(
            id="ev_1",
            step=4,
            kind="text",
            timestamp=ts,
            content="Navigation path required 4 clicks across 3 nested menus: Account -> Settings -> Membership & billing -> Manage plan.",
        ),
        Evidence(
            id="ev_2",
            step=4,
            kind="text",
            timestamp=ts,
            content="Primary CTA is 'Keep my Premium plan' (20px red button); cancel link 'I still want to cancel' is 11px muted grey.",
        ),
        Evidence(
            id="ev_3",
            step=5,
            kind="text",
            timestamp=ts,
            content="Wait! Get 50% off for 3 months. Only for you, only today.",
        ),
        Evidence(
            id="ev_4",
            step=6,
            kind="text",
            timestamp=ts,
            content="Are you sure? You'll lose all your favourite shows forever, and your family will miss movie night.",
        ),
    ]
    raw_signals = [
        FrictionSignal(
            id="sig_1",
            indicator="extra_steps",
            title="7 steps required to reach the cancellation boundary",
            severity="high",
            description="Reaching the final cancellation control takes 7 navigation steps instead of a direct 1-2 click exit.",
            step_refs=[1, 2, 3, 4, 5, 6, 7],
            evidence_ids=["ev_1"],
        ),
        FrictionSignal(
            id="sig_2",
            indicator="hidden_cancel",
            title="Cancel option buried 3 menus deep with de-emphasized styling",
            severity="high",
            description="The cancel link is hidden under Settings > Membership & billing > Manage plan and styled in low-contrast 11px text.",
            step_refs=[2, 3, 4],
            evidence_ids=["ev_1", "ev_2"],
        ),
        FrictionSignal(
            id="sig_3",
            indicator="retention_offer",
            title="Retention discount wall interrupts the exit path",
            severity="low",
            description="A '50% off for 3 months' interstitial must be dismissed before reaching confirmation.",
            step_refs=[5],
            evidence_ids=["ev_3"],
        ),
        FrictionSignal(
            id="sig_4",
            indicator="unclear_copy",
            title="Guilt-tripping confirmation dialog (confirm-shaming)",
            severity="medium",
            description="The confirmation screen uses emotional guilt ('your family will miss movie night') while highlighting 'Stay and keep watching'.",
            step_refs=[6],
            evidence_ids=["ev_4"],
        ),
    ]
    total_score, scored_signals = score_signals(raw_signals, evidence, total_steps=len(MOCK_STEPS))

    ccpa = [
        CcpaAlignment(
            pattern="subscription_trap",
            signal_ids=["sig_1", "sig_2"],
            rationale="Cancellation requires navigating a 7-step buried path and visually subordinated controls.",
        ),
        CcpaAlignment(
            pattern="interface_interference",
            signal_ids=["sig_2"],
            rationale="Visual hierarchy strongly favours 'Keep my Premium plan' over the 11px grey cancel action.",
        ),
        CcpaAlignment(
            pattern="nagging",
            signal_ids=["sig_3"],
            rationale="Retention interstitial interrupts the user's explicit intent to cancel.",
        ),
        CcpaAlignment(
            pattern="confirm_shaming",
            signal_ids=["sig_4"],
            rationale="Dialog copy uses guilt to steer the user away from cancelling.",
        ),
    ]
    return Report(
        run_id=run_id,
        service=service,
        outcome="completed_with_evidence",
        friction_score=total_score,
        safety_gate_stopped=True,
        stop_reason="pre_cancellation_boundary",
        friction_signals=scored_signals,
        evidence=evidence,
        ccpa_alignment=ccpa,
        limitations=[
            "DEMO FALLBACK DATA - deterministic mock audit path.",
            "Safety gate enforced: stopped before clicking final 'Confirm cancellation' button.",
        ],
    )
