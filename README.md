# ExitLens

**Audit Subscription Cancellation Friction Through Evidence, Transparency, and User Control.**

ExitLens is a web-based auditing tool that identifies potential friction in subscription cancellation journeys, links findings to supporting evidence, and maps relevant observations to consumer protection guidelines.

> **Note:** ExitLens is a decision-support tool. Final cancellation remains under user control.

## Features

- **Friction Detection:** Identifies potential barriers in cancellation workflows.
- **Evidence-Based Auditing:** Links findings to supporting evidence.
- **Regulatory Mapping:** Maps observations to relevant CCPA considerations.
- **Friction Assessment:** Evaluates potential cancellation complexity.
- **User Control:** Does not automate final cancellation.

## How It Works

1. Submit a cancellation journey.
2. Analyze the workflow.
3. Detect potential friction points.
4. Review evidence and regulatory mapping.
5. Make an informed decision.

## Tech Stack

| Component | Technologies |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript |
| Styling | Tailwind CSS, PostCSS |
| Icons | Lucide React |
| Backend | Python, FastAPI, Uvicorn |
| Audit Integration | TinyFish |
| Configuration | Pydantic, python-dotenv |

## Project Structure

```text
ExitLens-HACKIIITD/
├── backend/
├── frontend/
├── docs/
└── AGENTS.md
```

## Getting Started

**Prerequisites:** Git, Node.js, npm, Python 3.10+

**1. Clone Repository**

```bash
git clone https://github.com/Ritweek17/ExitLens-HACKIIITD.git
cd ExitLens-HACKIIITD
```

**2. Run Frontend**

```bash
cd frontend
npm install
npm run dev
```

**3. Run Backend**

```bash
cd backend
python -m venv .venv
```

Activate the environment:

```powershell
# Windows
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Install dependencies and start the server:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

**4. Environment Variables**

Configure the required credentials in a `.env` file. Never commit secrets.

## Privacy & Safety

- No automated final cancellation.
- Evidence-linked audit findings.
- Human review of automated observations.
- Protection of credentials and session data.
- Regulatory mapping is not legal advice.

## License

No license has been specified yet.

## Repository

[GitHub – ExitLens-HACKIIITD](https://github.com/Ritweek17/ExitLens-HACKIIITD)