# ExitLens backend

FastAPI backend for ExitLens. The v1 endpoints currently return **mock data**; the TinyFish runner gets wired in next.
API contract: [`../docs/api-contract.md`](../docs/api-contract.md). Interactive docs: http://localhost:8000/docs

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

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

Server: http://localhost:8000

| URL | What |
|---|---|
| `GET /health` | Health check |
| `POST /runs` | Create a run (needs `human_approved` and `test_account_confirmed` set to `true`) |
| `GET /runs/{run_id}/events` | SSE stream of steps (mock) |
| `GET /runs/{run_id}/report` | Friction report (mock) |
| `/demo-site/` | Fake OTT site with planted dark patterns, used as the audit target |
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
| `mock_data.py` | Canned steps and report used by the stubs |
| `scoring.py` | Friction score formula |
| `tinyfish_test.py` | Standalone TinyFish streaming test |
| `demo_site/` | Mock dark-pattern subscription site |
