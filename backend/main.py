"""ExitLens backend - FastAPI app."""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

DEFAULT_ORIGINS = "http://localhost:5173,http://localhost:3000"
ALLOWED_ORIGINS = [
    o.strip() for o in (os.getenv("ALLOWED_ORIGINS") or DEFAULT_ORIGINS).split(",") if o.strip()
]

app = FastAPI(title="ExitLens API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
