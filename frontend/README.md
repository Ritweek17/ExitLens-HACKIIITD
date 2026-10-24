# ExitLens Frontend

A Next.js 15 (App Router) frontend for **ExitLens**, an automated, evidence-linked subscription cancellation journey auditor.

## Tech Stack

- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS (Strictly preserving the ExitLens warm ivory `#FAF9F7` and deep charcoal aesthetic)
- **Streaming:** Native Browser `EventSource` (SSE)
- **Icons:** Lucide React

## Setup & Running Locally

### 1. Install dependencies
```bash
cd frontend
npm install
```

### 2. Configure Environment
```bash
cp .env.example .env.local
```
Ensure `NEXT_PUBLIC_API_BASE_URL` points to your ExitLens FastAPI backend:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 3. Run the Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Build for Production
```bash
npm run build
npm start
```

## Available Routes

- `/`: Landing page with hero, interactive dashboard preview, workflow explanation, and regulatory dark pattern overview.
- `/check`: Accessible audit creation form with searchable combobox, URL validation, and required safety confirmations.
- `/run/[run_id]`: Live SSE audit monitor displaying observed steps, live browser streaming preview, and safety boundary enforcement.
- `/report/[run_id]`: Verified evidence report with Box D friction scores, candidate CCPA alignments, DOM evidence excerpts, and print styling.
- `/how-it-works`: Three-step audit methodology, CCPA 2023 background, and FAQs.

## Safety Architecture

- **Pre-Cancellation Boundary:** ExitLens navigates up to the final cancellation action, names the button, and halts without clicking.
- **Dedicated Test Accounts:** Real personal accounts are never used; zero sensitive credentials or payment cards are stored.
