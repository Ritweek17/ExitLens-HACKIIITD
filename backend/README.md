# ExitLens backend

FastAPI backend for ExitLens. Implements the v1 Hackathon API contract ([`../docs/api-contract.md`](../docs/api-contract.md)), the TinyFish streaming orchestrator (`orchestrator.py`), the Box D deduplicated evidence-gated scoring engine (`scoring.py`), and the deterministic demo fallback (`mock_data.py`). Interactive docs: http://localhost:8000/docs

Requires **Python 3.11+** (the `tinyfish` SDK needs it).

## Setup (once)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then put your TINYFISH_API_KEY in .env
```

`.env` is git-ignored. Never commit it, and never send the TinyFish key to the frontend.

## Run the server

### Option A: One-command live TinyFish + public tunnel launcher (recommended for demo)

Automatically opens an HTTPS tunnel (`localhost.run`), sets `PUBLIC_DEMO_BASE_URL`, and starts FastAPI on `http://localhost:8000`:

```bash
cd backend
source venv/bin/activate
python start_live_demo.py
```

### Option B: Standard uvicorn server

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

Server: http://localhost:8000

| URL | What |
|---|---|
| `GET /health` | Health check |
| `GET /presets` | Curated Indian subscription presets (`StreamFlix India`, `GanaPlus Music`, `QuickCart Pro`, `CineVeil VIP`) |
| `POST /runs` | Create a run (needs `human_approved` and `test_account_confirmed` set to `true`) |
| `GET /runs/{run_id}/events` | SSE stream of steps (live TinyFish or deterministic demo fallback) |
| `GET /runs/{run_id}/report` | Evidence-gated friction report |
| `/demo-site/` | StreamFlix India demo target (buried cancel, retention wall, confirm-shaming) |
| `/demo-site/music.html` | GanaPlus Music demo target (FAQ redirect loop, mandatory survey, trick copy) |
| `/demo-site/fair.html` | QuickCart Pro demo target (clean 2-step CCPA-compliant benchmark) |
| `/demo-site/blocked.html` | CineVeil VIP demo target (Cloudflare Error 1200 / CAPTCHA + OTP barrier) |
| `/docs` | Swagger UI with the exact request/response models |

Quick check:

```bash
curl localhost:8000/health
RUN=$(curl -s -X POST localhost:8000/runs -H 'Content-Type: application/json' \
  -d '{"service":"Example OTT","human_approved":true,"test_account_confirmed":true}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["run_id"])')
curl -N localhost:8000/runs/$RUN/events
curl localhost:8000/runs/$RUN/report
```

CORS allows `http://localhost:5173` and `http://localhost:3000` by default. Override with a comma-separated `ALLOWED_ORIGINS` in `.env`.

## TinyFish smoke test

```bash
cd backend
source venv/bin/activate
python tinyfish_test.py https://example.com
python tinyfish_test.py https://example.com --goal "Find the pricing page and list the plans."
```

TinyFish runs in the cloud, so it cannot reach `localhost`. To audit the demo site, expose it publicly first (for example `ngrok http 8000`) and pass `https://<your-ngrok-host>/demo-site/`.

## Files

| File | Purpose |
|---|---|
| `main.py` | FastAPI app, CORS, endpoints |
| `models.py` | Pydantic models: the API contract in code |
| `orchestrator.py` | TinyFish streaming adapter, barrier/CAPTCHA detector, evidence normaliser, and mock fallback |
| `scoring.py` | Box D deduplicated indicator weights (`30/20/15/15/10/10`) and evidence-gating |
| `mock_data.py` | Curated Indian OTT presets, deterministic fallback steps, and reports |
| `test_backend.py` | Unit & integration tests for scoring, barrier detection, and API endpoints |
| `tinyfish_test.py` | Standalone TinyFish streaming test |
| `demo_site/` | Mock dark-pattern subscription sites (`index.html`, `music.html`, `fair.html`, `blocked.html`) |

## Run unit & integration tests

```bash
PYTHONPATH=backend backend/venv/bin/python -m unittest discover -s backend -p "test_*.py" -v
```
