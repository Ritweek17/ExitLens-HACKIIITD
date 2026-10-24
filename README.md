# ExitLens

**Audit subscription cancellation friction — with evidence, transparency, and user control.**

ExitLens is a tool designed to review subscription cancellation journeys and identify friction that may make it unnecessarily difficult for users to cancel a service. It aims to produce evidence-linked findings and map relevant observations to CCPA-related considerations, while keeping the final cancellation decision in the user's hands.

> **Important:** ExitLens is an auditing and decision-support tool. It does not automatically perform the final cancellation on a user's behalf.

## Table of Contents

- [Why ExitLens?](#why-exitlens)
- [Key Features](#key-features)
- [How It Works](#how-it-works)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Privacy and Safety](#privacy-and-safety)
- [License](#license)
- [Project Repository](#project-repository)

## Why ExitLens?

Subscription cancellation flows can contain confusing navigation, repeated steps, unclear wording, or other obstacles. ExitLens is intended to help make these experiences easier to inspect by documenting potential friction and connecting findings to supporting evidence.

The goal is to support clearer, more accountable cancellation experiences—not to take control away from the user.

## Key Features

- **Cancellation-flow friction audit:** Review a subscription cancellation journey for potential obstacles.
- **Evidence-linked findings:** Associate observations with evidence so reviewers can understand why a finding was raised.
- **CCPA-oriented mapping:** Help relate relevant findings to applicable California Consumer Privacy Act (CCPA) considerations. This is informational support, not legal advice or a legal compliance certification.
- **Human-in-the-loop control:** The user remains responsible for the final cancellation action.
- **Web-based interface:** A frontend for interacting with the auditing workflow.
- **Backend integration:** A Python API layer that includes TinyFish-related dependencies for the audit workflow.

> The exact checks and outputs depend on the implementation and the website being reviewed. An audit result should be treated as a finding to review, not as an automatic legal conclusion.

## How It Works

1. **Start an audit** — Provide or select the subscription cancellation journey to review.
2. **Inspect the flow** — The system examines relevant steps using the configured audit workflow.
3. **Review findings** — Potential friction points are presented alongside supporting evidence where available.
4. **Consider regulatory context** — Relevant findings may be mapped to CCPA-oriented considerations.
5. **Decide what to do** — The user reviews the results and decides whether to continue. ExitLens does not automatically execute the final cancellation.

## Technology Stack

The repository currently includes the following technologies and dependencies:

- **Frontend:** Next.js 15, React 19 (Web interface)
- **Frontend Language:** TypeScript (Typed JavaScript development)
- **Styling:** Tailwind CSS, PostCSS, Autoprefixer (UI styling and CSS processing)
- **Icons:** Lucide React (Interface icons)
- **Backend:** Python, FastAPI (API layer)
- **API Server:** Uvicorn (ASGI server)
- **Audit Integration:** TinyFish Python package (Website and audit workflow integration)
- **Configuration & Validation:** python-dotenv, Pydantic (Environment configuration and data validation)

## Project Structure

```text
ExitLens-HACKIIITD/
├── backend/       # Python API and audit workflow
├── frontend/      # Next.js web application
├── docs/          # Project documentation
└── AGENTS.md      # Repository-specific development guidance
```

## Getting Started

### Prerequisites

Install the following before running the project:

- Git
- Node.js and npm
- Python 3.10 or newer (use the version supported by your environment and dependencies)

### 1. Clone the repository

```bash
git clone https://github.com/Ritweek17/ExitLens-HACKIIITD.git
cd ExitLens-HACKIIITD
```

### 2. Set up the frontend

```bash
cd frontend
npm install
npm run dev
```

The Next.js development server usually runs at `http://localhost:3000`. Open that address in your browser if the terminal confirms it is available.

For a production build:

```bash
npm run build
npm start
```

### 3. Set up the backend

Open a second terminal from the repository root:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

**Windows PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI application:

```bash
uvicorn main:app --reload
```

If your backend entry point uses a different filename or application variable, adjust `main:app` accordingly.

### 4. Configure environment variables

If the backend or TinyFish integration requires credentials, create a `.env` file in the location expected by the application. Add only the variable names required by the code or official service documentation.

Example template:

```env
# Add the environment variables required by your backend here.
# Do not commit API keys, passwords, or other secrets.
```

Confirm required variables from the backend source code and the relevant TinyFish documentation before running the integration.

## Configuration

- Keep credentials in environment variables rather than hard-coding them.
- Do not commit `.env` files or access tokens.
- Confirm the frontend's API base URL matches the backend address used in your local environment.
- Follow the configuration and usage instructions provided by the current source code and TinyFish account setup.

## Privacy and Safety

ExitLens is designed around user oversight:

- **No automated final cancellation:** The tool should not submit the final cancellation action on the user's behalf.
- **Evidence matters:** Reviewers should be able to inspect the evidence behind findings where the implementation provides it.
- **Careful interpretation:** Automated observations may be incomplete or incorrect and should be reviewed.
- **Protect credentials and session data:** Do not publish passwords, cookies, tokens, or private account information in logs, screenshots, issues, or commits.
- **Regulatory context is not legal advice:** CCPA mapping is informational and does not establish compliance by itself.

## License

No license information was confirmed while preparing this README. Add the project's chosen license and include a `LICENSE` file before describing the repository as open source for reuse.

## Project Repository

[ExitLens-HACKIIITD on GitHub](https://github.com/Ritweek17/ExitLens-HACKIIITD)
