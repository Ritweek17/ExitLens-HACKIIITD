# ExitLens

**Auditing Subscription Cancellation Friction Through Evidence, Transparency, and User Control.**

ExitLens is a web-based auditing tool that analyzes subscription cancellation journeys to identify potential friction, document supporting evidence, and map relevant observations to consumer protection regulations.

It helps reviewers understand where cancellation processes may create unnecessary barriers while keeping the final decision and cancellation action under user control.

> **Note:** ExitLens is an auditing and decision-support tool. It does not automatically execute subscription cancellations or provide legal compliance certification.

## Key Features

- **Cancellation Friction Detection:** Identifies potential obstacles in subscription cancellation workflows.
- **Evidence-Linked Findings:** Connects detected friction signals to supporting evidence for transparent review.
- **Regulatory Mapping:** Maps relevant observations to applicable CCPA (Central Consumer Protection Authority) considerations.
- **Friction Assessment:** Presents identified issues to help reviewers evaluate the complexity of cancellation journeys.
- **Human-in-the-Loop Control:** Keeps the final cancellation decision with the user.
- **Web-Based Interface:** Provides an accessible interface for initiating audits and reviewing results.

## How It Works

1. **Initiate Audit** — Provide the subscription cancellation journey for inspection.
2. **Analyze Workflow** — The configured audit engine examines the cancellation process.
3. **Detect Friction** — Identify potential barriers and unnecessary steps.
4. **Review Evidence** — Examine supporting evidence and associated regulatory considerations.
5. **Make an Informed Decision** — Review the findings and retain control over the final cancellation action.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend Framework | Next.js 15, React 19 |
| Language | TypeScript |
| Styling | Tailwind CSS, PostCSS |
| Icons | Lucide React |
| Backend | Python, FastAPI |
| API Server | Uvicorn |
| Audit Integration | TinyFish |
| Configuration & Validation | python-dotenv, Pydantic |

## Project Structure

```text
ExitLens-HACKIIITD/
├── backend/       # API and audit workflow
├── frontend/      # Next.js application
├── docs/          # Project documentation
└── AGENTS.md      # Development guidelines
```

## Getting Started

### Prerequisites

- Git
- Node.js and npm
- Python 3.10+

### 1. Clone the Repository

```bash
git clone https://github.com/Ritweek17/ExitLens-HACKIIITD.git
cd ExitLens-HACKIIITD
```

### 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 3. Start the Backend

Open a separate terminal from the repository root:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

Install dependencies and start the API:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend entry point and application variable should match the actual project configuration.

### 4. Environment Configuration

Create a `.env` file in the backend's expected configuration directory and add the required environment variables.

```env
# Add required API credentials and configuration here.
```

Refer to the backend implementation and TinyFish documentation for the required variables.

## Privacy & Responsible Use

ExitLens follows a user-controlled auditing approach:

- **User Authority:** No automated final cancellation on behalf of the user.
- **Evidence Transparency:** Findings should be traceable to supporting evidence.
- **Responsible Interpretation:** Automated findings require human review.
- **Data Protection:** Credentials, session tokens, and private account information must remain protected.
- **Regulatory Disclaimer:** Regulatory mappings are informational and do not constitute legal advice or establish compliance.

## License

No license has currently been specified. A `LICENSE` file must be added before the repository can be distributed under an open-source license.

## Repository

[GitHub — ExitLens-HACKIIITD](https://github.com/Ritweek17/ExitLens-HACKIIITD)