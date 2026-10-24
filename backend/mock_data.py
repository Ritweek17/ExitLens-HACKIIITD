"""Mock run data used by the stub endpoints until the TinyFish runner is wired in."""

from datetime import datetime, timezone

from models import CcpaAlignment, Evidence, FrictionSignal, Report, RunEvent
from scoring import compute_friction_score

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
    signals = [
        FrictionSignal(
            id="sig_1",
            title="Cancel option buried 3 menus deep",
            severity="high",
            description="The cancel option is not on the account page; it takes three menu levels to reach it.",
            step_refs=[2, 3, 4],
            evidence_ids=["ev_1"],
        ),
        FrictionSignal(
            id="sig_2",
            title="Guilt-tripping confirmation dialog",
            severity="medium",
            description="The confirmation dialog uses shaming copy to discourage cancelling.",
            step_refs=[6],
            evidence_ids=["ev_2"],
        ),
        FrictionSignal(
            id="sig_3",
            title="Retention offer interrupts the flow",
            severity="low",
            description="A discount offer must be dismissed before continuing.",
            step_refs=[5],
            evidence_ids=["ev_3"],
        ),
    ]
    evidence = [
        Evidence(id="ev_1", step=4, kind="text", content="Settings > Membership & billing > Manage plan"),
        Evidence(id="ev_2", step=6, kind="text", content="Are you sure? You'll lose all your favourite shows forever."),
        Evidence(id="ev_3", step=5, kind="text", content="Wait! Get 50% off for 3 months."),
    ]
    ccpa = [
        CcpaAlignment(
            pattern="subscription_trap",
            signal_ids=["sig_1"],
            rationale="Cancellation is harder to find than sign-up.",
        ),
        CcpaAlignment(
            pattern="confirm_shaming",
            signal_ids=["sig_2"],
            rationale="Dialog copy uses guilt to steer the user away from cancelling.",
        ),
        CcpaAlignment(
            pattern="nagging",
            signal_ids=["sig_3"],
            rationale="Retention offer repeatedly interrupts the user's intended action.",
        ),
    ]
    return Report(
        run_id=run_id,
        service=service,
        friction_score=compute_friction_score(len(MOCK_STEPS), signals),
        safety_gate_stopped=True,
        stop_reason="pre_cancellation_boundary",
        friction_signals=signals,
        evidence=evidence,
        ccpa_alignment=ccpa,
        limitations=[
            "MOCK DATA - not produced by a real audit.",
            "Audit stopped before the final cancellation action.",
        ],
    )
