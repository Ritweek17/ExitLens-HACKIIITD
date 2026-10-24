"""ExitLens backend - FastAPI app.

v1 endpoints return MOCK data (see mock_data.py). Contract: docs/api-contract.md.
"""

import asyncio
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from mock_data import MOCK_STEPS, mock_report, mock_step_event, now
from models import ErrorResponse, Report, RunCreate, RunCreated, RunEvent

load_dotenv()

DEFAULT_ORIGINS = "http://localhost:5173,http://localhost:3000"
ALLOWED_ORIGINS = [
    o.strip() for o in (os.getenv("ALLOWED_ORIGINS") or DEFAULT_ORIGINS).split(",") if o.strip()
]
MOCK_STEP_DELAY_SECONDS = 1.0

app = FastAPI(title="ExitLens API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory run store: run_id -> run metadata. Fine for a one-day build.
RUNS: dict[str, dict] = {}


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code, self.code, self.message = status_code, code, message


@app.exception_handler(ApiError)
async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


def get_run(run_id: str) -> dict:
    run = RUNS.get(run_id)
    if run is None:
        raise ApiError(404, "run_not_found", f"No run with id '{run_id}'.")
    return run


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# Mock dark-pattern subscription site used as a safe, reliable audit target.
# TinyFish runs in the cloud, so expose this publicly (e.g. ngrok) for live runs.
app.mount(
    "/demo-site",
    StaticFiles(directory=Path(__file__).parent / "demo_site", html=True),
    name="demo-site",
)


@app.post(
    "/runs",
    status_code=201,
    response_model=RunCreated,
    responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def create_run(body: RunCreate) -> RunCreated:
    if not (body.human_approved and body.test_account_confirmed):
        raise ApiError(
            409,
            "approval_required",
            "Human approval and a dedicated test account are required before a run can start.",
        )
    if body.start_url is not None and body.start_url.scheme != "https":
        raise ApiError(422, "invalid_start_url", "start_url must use HTTPS.")

    run_id = f"run_{uuid.uuid4().hex[:8]}"
    RUNS[run_id] = {
        "service": body.service,
        "start_url": str(body.start_url) if body.start_url else None,
        "created_at": now(),
    }
    return RunCreated(run_id=run_id)


def sse(event: RunEvent) -> str:
    return f"data: {event.model_dump_json()}\n\n"


@app.get(
    "/runs/{run_id}/events",
    response_class=StreamingResponse,
    responses={
        200: {
            # `model` registers RunEvent in /docs; the actual body is text/event-stream.
            "model": RunEvent,
            "content": {"text/event-stream": {}},
            "description": "SSE stream; each `data:` line is one JSON RunEvent (schema shown).",
        },
        404: {"model": ErrorResponse},
    },
)
async def run_events(run_id: str) -> StreamingResponse:
    get_run(run_id)

    async def stream():
        # MOCK: replay canned steps. Replace with the TinyFish runner later.
        for i, label in enumerate(MOCK_STEPS, start=1):
            yield sse(mock_step_event(i, label))
            await asyncio.sleep(MOCK_STEP_DELAY_SECONDS)
        last = len(MOCK_STEPS)
        yield sse(
            RunEvent(
                type="stopped",
                step=last,
                label="Stopped before the final cancellation action",
                timestamp=now(),
                stop_reason="pre_cancellation_boundary",
            )
        )
        yield sse(RunEvent(type="report_ready", step=last, label="Report ready", timestamp=now()))

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get(
    "/runs/{run_id}/report",
    response_model=Report,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def run_report(run_id: str) -> Report:
    run = get_run(run_id)
    return mock_report(run_id, run["service"])
