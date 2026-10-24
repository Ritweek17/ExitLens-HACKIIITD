# ExitLens API contract (initial proposal)

This is a framework-neutral v1 proposal for storing supervised automated audits and generating evidence-linked reports. It does not prescribe a backend, database, browser automation library, or legal taxonomy.

## Contract rules

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

## Resources

### Audit

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

### Step

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

## Endpoints

### Request an audit

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

### Approve the service and test account

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

### Start the approved audit

`POST /api/v1/audits/{auditId}/start`

This is a human-only action that explicitly starts one run. It succeeds only after the service and dedicated test account have been approved. The runner must bind to that exact account reference and verify the authenticated account identity before interacting with the service.

Response: `202 Accepted`, with the updated `Audit` in `running` status. Record the human who initiated the run and the start time.

If the approved test account cannot be verified, do not continue the flow. Stop with `account_verification_failed`; never fall back to a real personal account or another unapproved account.

### Get an audit and its timeline

`GET /api/v1/audits/{auditId}`

Response: `200 OK`, with the `Audit` resource and its ordered `steps`.

### Stream live audit events

`GET /api/v1/audits/{auditId}/events`

Response: `200 OK` using `text/event-stream`. While an audit is running, emit an event for every observed step, followed by terminal `audit.stopped` and `report.ready` events as applicable. Each step event contains the stored `Step` resource so the human supervising the run can follow the runner in real time.

### Append an observed step

`POST /api/v1/audits/{auditId}/steps`

Request: a `Step` object without server-generated fields (`id` and `sequence`).

Response: `201 Created`, with the stored step.

Only a `running` audit accepts steps. The server assigns sequence numbers. Evidence references must belong to this audit. The caller must redact personal information before evidence is stored or linked. The runner may append steps only while bound to the approved, verified dedicated test account.

### Stop an audit

`POST /api/v1/audits/{auditId}/stop`

Request:

```json
{
  "reason": "pre_cancellation_boundary"
}
```

`reason` is one of `pre_cancellation_boundary`, `blocked`, `account_verification_failed`, `user_stopped`, or `error`.

Response: `200 OK`, with the updated `Audit` resource. Stopping is terminal for step collection. A `pre_cancellation_boundary` stop must be recorded before the final cancellation action is submitted.

### Get a report

`GET /api/v1/audits/{auditId}/report`

Response: `200 OK` when the report is ready. The report contains service details, the approval record, the dedicated test account reference, ordered steps, friction observations, candidate signals, evidence references, and limitations. Return `409 Conflict` if the audit has not stopped and the report is not ready.

## Error responses

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

## Security and privacy requirements

- Every run must use the exact registered dedicated test account approved by a human for that run. Never use a real personal account; if no approved test account is available, do not run the audit.
- Verify the authenticated account identity before browsing and stop if it differs from the approved account reference.
- Do not accept passwords, payment details, or session secrets in audit API payloads. Keep any test-account authentication material in a protected runner credential store, scoped to that account.
- Redact personal information from screenshots and visible text before persistence.
- Protect evidence URLs with access control; do not expose public, guessable evidence links.
- Validate URLs and evidence ownership, and apply request-size and rate limits.
- Define retention and deletion behavior before storing audit evidence.

## Open contract questions

- How are dedicated test accounts registered, verified, and securely provisioned to the runner?
- How does an audit runner authenticate and associate requests with a user or team?
- Should evidence be uploaded through this API or referenced from a separate private object store?
- Which screenshot, text, and navigation metadata formats are required for reproducibility?
- Is report generation synchronous at stop time or an asynchronous job?
- What are the permitted URL scope and redirect rules for an audit?
- What evidence retention period and deletion guarantees should the service expose?
