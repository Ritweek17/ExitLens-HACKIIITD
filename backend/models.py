"""Pydantic models for the ExitLens hackathon API (v1).

These shapes ARE the contract with the frontend (see docs/api-contract.md).
Change them only after agreeing with the frontend owner.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

# --- Enums -----------------------------------------------------------------

EventType = Literal["step", "stopped", "report_ready", "error"]

StopReason = Literal[
    "pre_cancellation_boundary",
    "blocked",
    "account_verification_failed",
    "user_stopped",
    "error",
]

# Box E: Audit verification & completion outcomes
AuditOutcome = Literal[
    "completed_with_evidence",
    "partial_evidence",
    "failed",
    "unverified",
    "human_required",
]

Severity = Literal["low", "medium", "high"]

# Box D: Deduped friction indicator categories (weights: 30/20/15/15/10/10 = 100 max)
FrictionIndicator = Literal[
    "extra_steps",      # Weight 30: Excessive navigation depth / clicks to reach cancel
    "hidden_cancel",    # Weight 20: Cancel link buried or visually de-emphasized
    "redirects",        # Weight 15: Misdirection, circular loops, or dead-end pages
    "forced_reason",    # Weight 15: Mandatory cancellation survey or reason selection
    "retention_offer",  # Weight 10: Discount/pause walls interrupting the exit flow
    "unclear_copy",     # Weight 10: Confirm-shaming, guilt copy, or confusing button labels
]

EvidenceKind = Literal["text", "screenshot", "url"]

# The 13 dark patterns listed in India's CCPA "Guidelines for Prevention and
# Regulation of Dark Patterns, 2023" (Central Consumer Protection Authority).
CcpaPattern = Literal[
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
]

# --- POST /runs ------------------------------------------------------------


class RunCreate(BaseModel):
    service: str = Field(..., min_length=1, examples=["Example OTT"])
    start_url: HttpUrl | None = Field(
        None,
        description="HTTPS page where the cancellation journey starts. Omit to run the deterministic demo fallback.",
        examples=["https://example.in/account/subscription"],
    )
    human_approved: bool = Field(
        ..., description="A human reviewed this exact service and approved the run. Must be true."
    )
    test_account_confirmed: bool = Field(
        ...,
        description="The run uses a dedicated test account (or no login), never a real personal account. Must be true.",
    )
    test_account_ref: str | None = Field(
        None,
        description="Optional server-managed dedicated test account reference (e.g. 'tacct_streamflix_in'). Verified against GET /test-accounts when supplied.",
        examples=["tacct_streamflix_in"],
    )


class RunCreated(BaseModel):
    run_id: str = Field(..., examples=["run_ab12cd34"])


class RunStopRequest(BaseModel):
    reason: StopReason = Field(
        "user_stopped",
        description="Reason the supervising human stopped the run.",
    )


class RunStopped(BaseModel):
    run_id: str
    status: Literal["stopped"] = "stopped"
    stop_reason: StopReason


class TestAccountPublic(BaseModel):
    id: str = Field(..., examples=["tacct_streamflix_in"])
    service: str = Field(..., examples=["StreamFlix India"])
    masked_identifier: str = Field(..., examples=["audit.streamflix@test.exitlens.in"])
    kind: Literal["dedicated_test"] = "dedicated_test"
    has_cloud_credentials: bool = Field(
        False,
        description="True when a TinyFish browser profile or credential vault item is bound to this test account.",
    )


class ServicePreset(BaseModel):
    id: str = Field(..., examples=["streamflix"])
    service: str = Field(..., examples=["StreamFlix India"])
    category: str = Field(..., examples=["Video OTT"])
    demo_path: str = Field(..., examples=["/demo-site/"])
    default_start_url: HttpUrl | None = Field(
        None,
        description="Real-world HTTPS cancellation/account entry URL for live external audits.",
        examples=["https://www.netflix.com/youraccount"],
    )
    default_test_account_ref: str | None = Field(
        None,
        description="Default registered dedicated test account ID for this preset.",
        examples=["tacct_streamflix_in"],
    )
    description: str
    expected_outcome: AuditOutcome = Field("completed_with_evidence")


# --- GET /runs/{run_id}/events (SSE `data:` payloads) -----------------------


class RunEvent(BaseModel):
    type: EventType
    step: int = Field(..., ge=0, description="Step number; terminal events repeat the last step number.")
    label: str = Field(..., examples=["Clicked 'Manage plan'"])
    timestamp: datetime
    screenshot_url: str | None = None
    streaming_url: str | None = Field(
        None, description="TinyFish live browser view URL, when available."
    )
    stop_reason: StopReason | None = Field(None, description="Set only on `stopped` events.")


# --- GET /runs/{run_id}/report ---------------------------------------------


class FrictionSignal(BaseModel):
    id: str = Field(..., examples=["sig_1"])
    indicator: FrictionIndicator = Field(
        "unclear_copy",
        description="Box D indicator category used for deduplicated weighted scoring.",
    )
    title: str
    severity: Severity
    weight: int = Field(
        0,
        ge=0,
        le=30,
        description="Actual points contributed to friction_score (0 if unverified or duplicate indicator).",
    )
    verified: bool = Field(
        True,
        description="True only when backed by captured evidence; unverified signals contribute 0 points.",
    )
    description: str
    step_refs: list[int] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    id: str = Field(..., examples=["ev_1"])
    step: int
    kind: EvidenceKind
    timestamp: datetime | None = Field(
        None, description="When this evidence was captured during the run."
    )
    content: str | None = Field(None, description="Visible text or a description of the evidence.")
    url: str | None = Field(None, description="Screenshot or page URL, when applicable.")


class CcpaAlignment(BaseModel):
    pattern: CcpaPattern
    signal_ids: list[str] = Field(default_factory=list)
    status: Literal["candidate"] = Field(
        "candidate", description="Always a candidate for human review, never a legal finding."
    )
    rationale: str


class Report(BaseModel):
    run_id: str
    service: str
    outcome: AuditOutcome = Field(
        "completed_with_evidence",
        description="Box E verification outcome of the audit session.",
    )
    friction_score: int = Field(..., ge=0, le=100)
    safety_gate_stopped: bool = Field(
        ..., description="True if the agent stopped before the final irreversible cancellation action."
    )
    stop_reason: StopReason
    test_account_ref: str | None = Field(
        None, description="Verified dedicated test account reference used for this run, when bound."
    )
    account_verified: bool = Field(
        True,
        description="True when the runner verified it did not encounter an unapproved/personal account mismatch.",
    )
    streaming_url: str | None = Field(
        None, description="TinyFish live browser stream URL if captured during the run."
    )
    friction_signals: list[FrictionSignal]
    evidence: list[Evidence]
    ccpa_alignment: list[CcpaAlignment]
    limitations: list[str]


# --- Errors ----------------------------------------------------------------


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
