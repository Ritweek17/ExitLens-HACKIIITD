# ExitLens API contract

This file has two parts:

- **v1 - Hackathon contract (current, implemented).** The frontend builds against this. The backend serves exactly these shapes, and FastAPI's `/docs` page (http://localhost:8000/docs) shows the same models (`backend/models.py`). **Do not change v1 shapes without telling the other side.**
- **v2 - Full audit contract (post-hackathon target).** The original framework-neutral proposal, kept unchanged for later.

---

## v1 - Hackathon contract

### Rules

- Base URL (local): `http://localhost:8000`. No path prefix.
- JSON bodies; timestamps are ISO 8601 UTC; IDs are opaque strings.
- The TinyFish API key stays on the server. The frontend never calls TinyFish directly.
- A run starts only if a human approved it **and** confirmed that a dedicated test account (or no login) is used. A real personal account is never used.
- The agent must stop **before** the final cancellation action. No endpoint ever cancels a subscription.
- `ccpa_alignment` entries refer to India's **Central Consumer Protection Authority (CCPA) Guidelines for Prevention and Regulation of Dark Patterns, 2023**. They are always `"candidate"` annotations for human review, never legal findings.

### `GET /health`

`200 OK` -> `{"status": "ok"}`

### `POST /runs`

Create and start an audit run.

Request:

```json
{
  "service": "Example OTT",
  "start_url": "https://example.in/account/subscription",
  "human_approved": true,
  "test_account_confirmed": true
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `service` | string | yes | Non-empty service name. |
| `start_url` | string (URL) | no | Must be `https://` when given. |
| `human_approved` | boolean | yes | Must be `true`. |
| `test_account_confirmed` | boolean | yes | Must be `true`. |

Responses:

- `201 Created` -> `{"run_id": "run_ab12cd34"}`
- `409 Conflict` -> `{"error": {"code": "approval_required", "message": "..."}}` when either approval flag is not `true`.
- `422 Unprocessable Entity` -> missing or invalid fields (FastAPI's default validation body), or `{"error": {"code": "invalid_start_url", ...}}` for a non-HTTPS `start_url`.

### `GET /runs/{run_id}/events`

Server-Sent Events stream (`text/event-stream`). Every message uses only `data:` lines (no custom `event:` names), so a plain `EventSource.onmessage` handler gets everything. Each `data:` payload is one JSON `RunEvent`:

```json
{
  "type": "step",
  "step": 3,
  "label": "Clicked 'Manage plan'",
  "timestamp": "2026-10-24T12:03:00Z",
  "screenshot_url": null,
  "streaming_url": null,
  "stop_reason": null
}
```

| Field | Type | Notes |
|---|---|---|
| `type` | `"step"` \| `"stopped"` \| `"report_ready"` \| `"error"` | |
| `step` | integer >= 0 | Terminal events repeat the last step number. |
| `label` | string | Human-readable description of the step. |
| `timestamp` | string (ISO 8601) | |
| `screenshot_url` | string \| null | Optional; may stay null. |
| `streaming_url` | string \| null | TinyFish live browser view, when available. |
| `stop_reason` | `"pre_cancellation_boundary"` \| `"blocked"` \| `"user_stopped"` \| `"error"` \| null | Set only on `stopped` events. |

Event order: one or more `step` -> `stopped` -> `report_ready`. On failure an `error` event is sent instead. **After `report_ready` or `error`, the server closes the stream; the client should call `eventSource.close()`** (otherwise `EventSource` reconnects automatically).

`404 Not Found` (`run_not_found`) for an unknown `run_id`.

### `GET /runs/{run_id}/report`

`200 OK` -> `Report`:

```json
{
  "run_id": "run_ab12cd34",
  "service": "Example OTT",
  "friction_score": 60,
  "safety_gate_stopped": true,
  "stop_reason": "pre_cancellation_boundary",
  "friction_signals": [
    {
      "id": "sig_1",
      "title": "Cancel option buried 3 menus deep",
      "severity": "high",
      "description": "The cancel option is not on the account page; it takes three menu levels to reach it.",
      "step_refs": [2, 3, 4],
      "evidence_ids": ["ev_1"]
    }
  ],
  "evidence": [
    { "id": "ev_1", "step": 4, "kind": "text", "content": "Settings > Membership & billing > Manage plan", "url": null }
  ],
  "ccpa_alignment": [
    { "pattern": "subscription_trap", "signal_ids": ["sig_1"], "status": "candidate", "rationale": "Cancellation is harder to find than sign-up." }
  ],
  "limitations": ["Audit stopped before the final cancellation action."]
}
```

| Field | Type | Notes |
|---|---|---|
| `friction_score` | integer 0-100 | See formula below. |
| `safety_gate_stopped` | boolean | `true` = the agent reported stopping before the final cancellation action. |
| `stop_reason` | same enum as events | |
| `friction_signals[].severity` | `"low"` \| `"medium"` \| `"high"` | |
| `friction_signals[].step_refs` / `evidence_ids` | arrays | Links each finding back to steps and evidence. |
| `evidence[].kind` | `"text"` \| `"screenshot"` \| `"url"` | |
| `ccpa_alignment[].pattern` | one of the 13 CCPA patterns below | |
| `ccpa_alignment[].status` | always `"candidate"` | |
| `limitations` | string[] | Where the audit stopped, what was not checked, etc. |

CCPA pattern values: `false_urgency`, `basket_sneaking`, `confirm_shaming`, `forced_action`, `subscription_trap`, `interface_interference`, `bait_and_switch`, `drip_pricing`, `disguised_advertisement`, `nagging`, `trick_question`, `saas_billing`, `rogue_malwares`.

Errors: `404` (`run_not_found`). Once real runs are wired in, `409` (`report_not_ready`) is returned until the run has stopped - the frontend should handle it (e.g. wait for the `report_ready` event before fetching). The current stub returns the mock report immediately.

### Friction score formula

```
score = min(100, extra_steps * 5 + sum(severity weights))
extra_steps = steps to reach the final cancel button beyond a 2-step baseline
severity weights: low = 5, medium = 10, high = 20
```

### Safety gate

1. **Prompt:** the TinyFish goal tells the agent to stop at the final cancel/confirm button, name it, and not click it.
2. **Structured output:** the agent must report the button it stopped at.
3. **Backend check:** if the agent's result indicates a cancellation was completed or confirmed, the backend sets `safety_gate_stopped: false` and flags it in `limitations`.

This is a best-effort guarantee for an AI browser agent, and the report says so.

### Error shape

```json
{ "error": { "code": "approval_required", "message": "Human approval and a dedicated test account are required." } }
```

Codes in v1: `approval_required` (409), `invalid_start_url` (422), `run_not_found` (404), `report_not_ready` (409, once real runs are wired in). FastAPI request-validation errors (422) keep FastAPI's default `{"detail": [...]}` body.

---

## v2 - Full audit contract (post-hackathon target)

The original proposal below is kept unchanged for after the hackathon. It is **not** implemented in v1. (Its own text calls itself "v1"; that refers to its `/api/v1` base path, not the hackathon contract above.)

### ExitLens API contract (initial proposal)

This is a framework-neutral v1 proposal for storing supervised automated audits and generating evidence-linked reports. It does not prescribe a backend, database, browser automation library, or legal taxonomy.

#### Contract rules

- Base path: `/api/v1`.
- JSON request and response bodies use `application/json` unless uploading evidence bytes.
- IDs are opaque strings. Timestamps are ISO 8601 UTC values.
- Every run requires explicit human approval of the exact service and its dedicated test account, followed by an explicit human start action.
- Every run uses a registered, approved dedicated test account. A real personal account is never used. If an approved dedicated test account cannot be bound to the runner and verified, the run must not start or must stop immediately.
- The test account reference resolves to a server-managed account classified as `dedicated_test`; a request cannot create or relabel a personal account as a test account.
- The runner streams every observed step while running.
- An audit records observations and produces a report; it does not change the audited subscription.
- There is no API operation for cancelling a subscription. The runner must stop before any final cancellation action.
- Candidate CCPA signal labels are review annotations. The API and report must not present them as legal findings.

#### Resources

##### Audit

```json
{
  "id": "aud_123",
  "service": {
    "name": "Example Service",
    "startUrl": "https://example.in/account/subscription"
  },
  "countryCode": "IN",
  "status": "pending_approval",
  "testAccount": null,
  "approval": null,
  "createdAt": "2026-10-24T12:00:00Z",
  "startedAt": null,
  "stoppedAt": null,
  "stopReason": null,
  "stepCount": 0,
  "reportUrl": null
}
```

`status` is one of `pending_approval`, `approved`, `running`, `stopped`, or `report_ready`.

Once approved, `testAccount` contains the approved server-managed reference and its server-verified kind:

```json
{
  "reference": "tacct_123",
  "kind": "dedicated_test"
}
```

`approval` records the human gate:

```json
{
  "serviceApproved": true,
  "testAccountApproved": true,
  "approvedBy": "usr_123",
  "approvedAt": "2026-10-24T12:02:00Z"
}
```

`stopReason` is one of `pre_cancellation_boundary`, `blocked`, `account_verification_failed`, `user_stopped`, or `error`. A `pre_cancellation_boundary` outcome means the runner stopped before submitting the final cancellation action.

##### Step

Steps are append-only and ordered by `sequence`. They describe actions already observed by the audit runner; this endpoint is not an instruction to perform an action.

```json
{
  "id": "step_001",
  "sequence": 1,
  "observedAt": "2026-10-24T12:03:00Z",
  "pageUrl": "https://example.in/account/subscription",
  "action": {
    "type": "click",
    "targetLabel": "Manage plan"
  },
  "result": {
    "summary": "Opened the subscription management page",
    "visibleText": "Manage your plan"
  },
  "evidence": [
    {
      "id": "ev_001",
      "kind": "screenshot",
      "url": "https://evidence.example/ev_001",
      "capturedAt": "2026-10-24T12:03:00Z",
      "redacted": true
    }
  ],
  "frictionObservations": [],
  "candidateSignals": []
}
```

Allowed observed action types are `navigate`, `click`, `type`, `select`, `scroll`, and `wait`. The runner must not execute or record a final cancellation submission as an ordinary step. If the next action would submit cancellation, stop the audit and set `stopReason` to `pre_cancellation_boundary`.

`frictionObservations` contains plain-language descriptions grounded in the step. `candidateSignals` contains optional review annotations, each with a label, rationale, and supporting evidence IDs. Both are empty unless there is an observed basis for them.

#### Endpoints

##### Request an audit

`POST /api/v1/audits`

Request:

```json
{
  "service": {
    "name": "Example Service",
    "startUrl": "https://example.in/account/subscription"
  },
  "countryCode": "IN"
}
```

Response: `201 Created`, with a new `Audit` in `pending_approval` status. Creating an audit does not start the runner.

The start URL must use HTTPS. The API stores service and audit metadata, not login credentials.

##### Approve the service and test account

`POST /api/v1/audits/{auditId}/approve`

This is a human-only action. The human must review the exact service and approve a registered dedicated test account before the run can start.

Request:

```json
{
  "serviceApproved": true,
  "testAccountApproved": true,
  "testAccountRef": "tacct_123"
}
```

`testAccountRef` must resolve server-side to a registered account classified as `dedicated_test`. `approvedBy` and `approvedAt` are taken from the authenticated human identity and server clock, not from caller-supplied fields. Missing or false approval values, an unregistered account, or an account not classified as a dedicated test account are rejected.

Response: `200 OK`, with the updated `Audit` in `approved` status and its approval record. Approval alone does not start the runner.

##### Start the approved audit

`POST /api/v1/audits/{auditId}/start`

This is a human-only action that explicitly starts one run. It succeeds only after the service and dedicated test account have been approved. The runner must bind to that exact account reference and verify the authenticated account identity before interacting with the service.

Response: `202 Accepted`, with the updated `Audit` in `running` status. Record the human who initiated the run and the start time.

If the approved test account cannot be verified, do not continue the flow. Stop with `account_verification_failed`; never fall back to a real personal account or another unapproved account.

##### Get an audit and its timeline

`GET /api/v1/audits/{auditId}`

Response: `200 OK`, with the `Audit` resource and its ordered `steps`.

##### Stream live audit events

`GET /api/v1/audits/{auditId}/events`

Response: `200 OK` using `text/event-stream`. While an audit is running, emit an event for every observed step, followed by terminal `audit.stopped` and `report.ready` events as applicable. Each step event contains the stored `Step` resource so the human supervising the run can follow the runner in real time.

##### Append an observed step

`POST /api/v1/audits/{auditId}/steps`

Request: a `Step` object without server-generated fields (`id` and `sequence`).

Response: `201 Created`, with the stored step.

Only a `running` audit accepts steps. The server assigns sequence numbers. Evidence references must belong to this audit. The caller must redact personal information before evidence is stored or linked. The runner may append steps only while bound to the approved, verified dedicated test account.

##### Stop an audit

`POST /api/v1/audits/{auditId}/stop`

Request:

```json
{
  "reason": "pre_cancellation_boundary"
}
```

`reason` is one of `pre_cancellation_boundary`, `blocked`, `account_verification_failed`, `user_stopped`, or `error`.

Response: `200 OK`, with the updated `Audit` resource. Stopping is terminal for step collection. A `pre_cancellation_boundary` stop must be recorded before the final cancellation action is submitted.

##### Get a report

`GET /api/v1/audits/{auditId}/report`

Response: `200 OK` when the report is ready. The report contains service details, the approval record, the dedicated test account reference, ordered steps, friction observations, candidate signals, evidence references, and limitations. Return `409 Conflict` if the audit has not stopped and the report is not ready.

#### Error responses

Errors use a stable JSON shape:

```json
{
  "error": {
    "code": "audit_not_approved",
    "message": "A human must approve the service and a dedicated test account before starting the audit."
  }
}
```

Expected status codes:

- `400 Bad Request` for malformed input or invalid enum values.
- `401 Unauthorized` or `403 Forbidden` when a human-only action is not authenticated or authorized.
- `404 Not Found` when the audit, test account, or evidence reference does not exist.
- `409 Conflict` when an operation is invalid for the audit's current state or the account is not an approved dedicated test account.
- `413 Content Too Large` when evidence exceeds configured limits.
- `422 Unprocessable Entity` when a URL or resource reference fails validation.

#### Security and privacy requirements

- Every run must use the exact registered dedicated test account approved by a human for that run. Never use a real personal account; if no approved test account is available, do not run the audit.
- Verify the authenticated account identity before browsing and stop if it differs from the approved account reference.
- Do not accept passwords, payment details, or session secrets in audit API payloads. Keep any test-account authentication material in a protected runner credential store, scoped to that account.
- Redact personal information from screenshots and visible text before persistence.
- Protect evidence URLs with access control; do not expose public, guessable evidence links.
- Validate URLs and evidence ownership, and apply request-size and rate limits.
- Define retention and deletion behavior before storing audit evidence.

#### Open contract questions

- How are dedicated test accounts registered, verified, and securely provisioned to the runner?
- How does an audit runner authenticate and associate requests with a user or team?
- Should evidence be uploaded through this API or referenced from a separate private object store?
- Which screenshot, text, and navigation metadata formats are required for reproducibility?
- Is report generation synchronous at stop time or an asynchronous job?
- What are the permitted URL scope and redirect rules for an audit?
- What evidence retention period and deletion guarantees should the service expose?
