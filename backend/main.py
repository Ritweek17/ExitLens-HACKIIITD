"""ExitLens backend - FastAPI app.

Implements the v1 Hackathon Contract (docs/api-contract.md) and the
Box B / D / E pipeline (orchestrator.py, scoring.py, mock_data.py).
"""

import os
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from mock_data import PRESETS, mock_report, now
from models import ErrorResponse, Report, RunCreate, RunCreated, RunEvent, ServicePreset
from orchestrator import is_start_url_allowed, should_use_live_tinyfish, stream_audit_run

load_dotenv()

DEFAULT_ORIGINS = "http://localhost:5173,http://localhost:3000"
ALLOWED_ORIGINS = [
    o.strip() for o in (os.getenv("ALLOWED_ORIGINS") or DEFAULT_ORIGINS).split(",") if o.strip()
]
MOCK_STEP_DELAY_SECONDS = 0.6


def _env_positive_int(name: str, default: int) -> int:
    try:
        value = int((os.getenv(name) or "").strip())
    except ValueError:
        return default
    return value if value > 0 else default


# In-memory run store limits (finished/idle runs only; active runs are never evicted).
MAX_RUNS = _env_positive_int("MAX_RUNS", 200)
RUN_TTL_SECONDS = _env_positive_int("RUN_TTL_SECONDS", 3600)

app = FastAPI(title="ExitLens API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory run store: run_id -> run metadata, events, and report.
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


def _is_active(run: dict) -> bool:
    """A run is active while its audit task has started and not yet finished."""
    return "task" in run and not run.get("done", False)


def prune_runs(now_mono: float | None = None) -> None:
    """Drop expired runs, then the oldest inactive runs while the store exceeds MAX_RUNS."""
    now_mono = time.monotonic() if now_mono is None else now_mono
    for rid in [
        rid
        for rid, run in RUNS.items()
        if not _is_active(run) and now_mono - run["created_mono"] > RUN_TTL_SECONDS
    ]:
        del RUNS[rid]
    # dicts keep insertion order, so iteration is oldest-first
    for rid in [rid for rid, run in RUNS.items() if not _is_active(run)]:
        if len(RUNS) <= MAX_RUNS:
            break
        del RUNS[rid]


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/presets", response_model=list[ServicePreset])
def list_presets() -> list[ServicePreset]:
    return PRESETS


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
    if not is_start_url_allowed(str(body.start_url) if body.start_url else None):
        raise ApiError(
            422,
            "host_not_allowed",
            "This server only audits allow-listed hosts (ALLOWED_AUDIT_HOSTS). Use a preset or ask the operator to allow this host.",
        )

    prune_runs()
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    RUNS[run_id] = {
        "service": body.service,
        "start_url": str(body.start_url) if body.start_url else None,
        "created_at": now(),
        "created_mono": time.monotonic(),
        "events": None,
        "report": None,
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
    run = get_run(run_id)

    async def stream():
        async for ev in stream_audit_run(run_id, run, mock_delay_seconds=MOCK_STEP_DELAY_SECONDS):
            yield sse(ev)

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
    if run.get("report") is not None:
        return run["report"]
    if not should_use_live_tinyfish(run.get("start_url"), run["service"]):
        run["report"] = mock_report(run_id, run["service"], run.get("start_url"))
        return run["report"]
    raise ApiError(
        409,
        "report_not_ready",
        "Audit is still running or has not streamed events yet. Wait for the `report_ready` SSE event.",
    )
