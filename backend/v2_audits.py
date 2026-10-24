"""v2 Full Audit Contract router (`/api/v1/audits`) backed by the ExitLens orchestrator.

Implements the multi-stage human gate (`pending_approval` -> `approved` -> `running` ->
`stopped` / `report_ready`) defined in the v2 section of `docs/api-contract.md` while sharing
the same test-account registry and orchestrator as v1 `/runs`.
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, HttpUrl

from mock_data import now
from models import ErrorResponse, Report, RunEvent, StopReason
from orchestrator import (
    _drive_audit,
    is_start_url_allowed,
    stop_audit_run,
    stream_audit_run,
)
from test_accounts import verify_dedicated_test_account

AuditStatus = Literal["pending_approval", "approved", "running", "stopped", "report_ready"]


class AuditServiceSpec(BaseModel):
    name: str = Field(..., min_length=1, examples=["StreamFlix India"])
    startUrl: HttpUrl | None = Field(
        None, examples=["https://example.in/account/subscription"]
    )


class AuditCreateRequest(BaseModel):
    service: AuditServiceSpec
    countryCode: str = Field("IN", min_length=2, max_length=2)


class AuditApproveRequest(BaseModel):
    serviceApproved: bool
    testAccountApproved: bool
    testAccountRef: str = Field(..., min_length=1, examples=["tacct_streamflix_in"])


class AuditStopRequest(BaseModel):
    reason: StopReason = "pre_cancellation_boundary"


class TestAccountBinding(BaseModel):
    reference: str
    kind: Literal["dedicated_test"] = "dedicated_test"


class ApprovalRecord(BaseModel):
    serviceApproved: bool
    testAccountApproved: bool
    approvedBy: str
    approvedAt: datetime


class AuditResource(BaseModel):
    id: str
    service: AuditServiceSpec
    countryCode: str = "IN"
    status: AuditStatus
    testAccount: TestAccountBinding | None = None
    approval: ApprovalRecord | None = None
    createdAt: datetime
    startedAt: datetime | None = None
    stoppedAt: datetime | None = None
    stopReason: StopReason | None = None
    stepCount: int = 0
    reportUrl: str | None = None
    steps: list[RunEvent] | None = None


def build_v2_router(
    runs_store: dict[str, dict[str, Any]],
    prune_fn: Any,
    api_error_cls: Any,
    mock_delay_getter: Any,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/audits", tags=["v2-audits"])

    def _get_audit_state(audit_id: str) -> dict[str, Any]:
        state = runs_store.get(audit_id)
        if state is None:
            raise api_error_cls(404, "audit_not_found", f"No audit with id '{audit_id}'.")
        return state

    def _to_resource(audit_id: str, state: dict[str, Any], include_steps: bool = False) -> AuditResource:
        events: list[RunEvent] = state.get("buffer") or state.get("events") or []
        step_events = [e for e in events if e.type == "step"]
        report: Report | None = state.get("report")

        if state.get("done") and report is not None:
            status: AuditStatus = "report_ready"
            stop_reason: StopReason | None = report.stop_reason
            stopped_at = state.get("stopped_at") or now()
            state["stopped_at"] = stopped_at
            report_url: str | None = f"/api/v1/audits/{audit_id}/report"
        else:
            status = state.get("v2_status", "pending_approval")
            stop_reason = state.get("stop_requested")
            stopped_at = state.get("stopped_at")
            report_url = None

        return AuditResource(
            id=audit_id,
            service=AuditServiceSpec(
                name=state["service"],
                startUrl=state.get("start_url"),
            ),
            countryCode=state.get("country_code", "IN"),
            status=status,
            testAccount=state.get("v2_test_account"),
            approval=state.get("v2_approval"),
            createdAt=state["created_at"],
            startedAt=state.get("started_at"),
            stoppedAt=stopped_at,
            stopReason=stop_reason,
            stepCount=len(step_events),
            reportUrl=report_url,
            steps=step_events if include_steps else None,
        )

    @router.post(
        "",
        status_code=201,
        response_model=AuditResource,
        responses={422: {"model": ErrorResponse}},
    )
    def create_audit(body: AuditCreateRequest) -> AuditResource:
        if body.service.startUrl is not None and body.service.startUrl.scheme != "https":
            raise api_error_cls(422, "invalid_start_url", "startUrl must use HTTPS.")
        start_url_str = str(body.service.startUrl) if body.service.startUrl else None
        if not is_start_url_allowed(start_url_str):
            raise api_error_cls(
                422,
                "host_not_allowed",
                "This server only audits allow-listed hosts (ALLOWED_AUDIT_HOSTS).",
            )

        prune_fn()
        audit_id = f"aud_{uuid.uuid4().hex[:8]}"
        state: dict[str, Any] = {
            "service": body.service.name,
            "start_url": start_url_str,
            "country_code": body.countryCode.upper(),
            "v2_status": "pending_approval",
            "v2_test_account": None,
            "v2_approval": None,
            "test_account_ref": None,
            "created_at": now(),
            "created_mono": time.monotonic(),
            "started_at": None,
            "stopped_at": None,
            "events": None,
            "report": None,
        }
        runs_store[audit_id] = state
        return _to_resource(audit_id, state)

    @router.post(
        "/{audit_id}/approve",
        response_model=AuditResource,
        responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    )
    def approve_audit(audit_id: str, body: AuditApproveRequest) -> AuditResource:
        state = _get_audit_state(audit_id)
        if state.get("v2_status") not in ("pending_approval", "approved"):
            raise api_error_cls(
                409,
                "invalid_audit_state",
                "Only a pending_approval audit can be approved.",
            )
        if not (body.serviceApproved and body.testAccountApproved):
            raise api_error_cls(
                409,
                "approval_required",
                "Both serviceApproved and testAccountApproved must be true.",
            )
        acct = verify_dedicated_test_account(body.testAccountRef)
        if acct is None:
            raise api_error_cls(
                409,
                "account_verification_failed",
                f"Test account '{body.testAccountRef}' is not a registered dedicated_test account.",
            )

        state["test_account_ref"] = acct.id
        state["v2_test_account"] = TestAccountBinding(reference=acct.id, kind="dedicated_test")
        state["v2_approval"] = ApprovalRecord(
            serviceApproved=True,
            testAccountApproved=True,
            approvedBy="human_supervisor",
            approvedAt=now(),
        )
        state["v2_status"] = "approved"
        return _to_resource(audit_id, state)

    @router.post(
        "/{audit_id}/start",
        status_code=202,
        response_model=AuditResource,
        responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    )
    async def start_audit(audit_id: str) -> AuditResource:
        state = _get_audit_state(audit_id)
        if state.get("v2_status") != "approved":
            raise api_error_cls(
                409,
                "audit_not_approved",
                "A human must approve the service and a dedicated test account before starting the audit.",
            )
        acct_ref = state.get("test_account_ref")
        if not acct_ref or verify_dedicated_test_account(acct_ref) is None:
            stop_audit_run(audit_id, state, reason="account_verification_failed")
            raise api_error_cls(
                409,
                "account_verification_failed",
                "Approved dedicated test account could not be verified at start time.",
            )

        state["v2_status"] = "running"
        state["started_at"] = now()
        state.setdefault("buffer", [])
        if "task" not in state:
            state["cond"] = asyncio.Condition()
            state["task"] = asyncio.create_task(
                _drive_audit(audit_id, state, mock_delay_getter())
            )
        return _to_resource(audit_id, state)

    @router.get(
        "/{audit_id}",
        response_model=AuditResource,
        responses={404: {"model": ErrorResponse}},
    )
    def get_audit(audit_id: str) -> AuditResource:
        state = _get_audit_state(audit_id)
        return _to_resource(audit_id, state, include_steps=True)

    @router.get(
        "/{audit_id}/events",
        response_class=StreamingResponse,
        responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    )
    async def audit_events(audit_id: str) -> StreamingResponse:
        state = _get_audit_state(audit_id)
        if state.get("v2_status") in ("pending_approval", "approved") and not state.get("done"):
            raise api_error_cls(
                409,
                "audit_not_started",
                "Audit must be approved and explicitly started before streaming events.",
            )

        async def stream():
            async for ev in stream_audit_run(audit_id, state, mock_delay_seconds=mock_delay_getter()):
                yield f"data: {ev.model_dump_json()}\n\n"

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @router.post(
        "/{audit_id}/stop",
        response_model=AuditResource,
        responses={404: {"model": ErrorResponse}},
    )
    def stop_audit(audit_id: str, body: AuditStopRequest | None = None) -> AuditResource:
        state = _get_audit_state(audit_id)
        reason = body.reason if body is not None else "user_stopped"
        stop_audit_run(audit_id, state, reason=reason)
        state["v2_status"] = "stopped"
        state["stopped_at"] = now()
        return _to_resource(audit_id, state, include_steps=True)

    @router.get(
        "/{audit_id}/report",
        response_model=Report,
        responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    )
    def audit_report(audit_id: str) -> Report:
        state = _get_audit_state(audit_id)
        if state.get("report") is not None:
            return state["report"]
        raise api_error_cls(
            409,
            "report_not_ready",
            "Audit has not finished or has not been started yet.",
        )

    return router
