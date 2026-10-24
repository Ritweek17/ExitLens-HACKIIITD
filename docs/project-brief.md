# ExitLens project brief

## Summary

ExitLens audits how difficult it is to cancel an online subscription in India. It walks the cancellation journey as a real user would, records each observed step, and produces an evidence-linked report describing friction and possible CCPA dark-pattern signals.

ExitLens stops before the final action that would cancel the subscription. It documents the journey; it never completes cancellation.

## Problem

People may have to navigate confusing, repetitive, or hard-to-find steps to cancel an online subscription. A useful audit needs to show what the user encountered, where it happened, and what evidence supports each finding. A summary without a reproducible trail is difficult to verify or act on.

## Product goal

Make subscription cancellation flows in India observable and reviewable by producing a step-by-step record with evidence links and clearly qualified friction findings.

## Default operating mode

ExitLens uses an **automated runner supervised by a human**. The runner performs the cancellation-flow audit and streams every observed step. A human starts each run and must approve the exact service and a registered, dedicated test account before the runner begins.

Every run uses an approved dedicated test account. ExitLens must never use a real person's personal account. If an approved dedicated test account is unavailable or the runner cannot verify that it is using the approved account, the run must not start or must stop safely.

## Intended users

- Consumers and consumer advocates examining a subscription's cancellation journey.
- Researchers or reviewers comparing cancellation experiences across services.
- Product and policy teams using documented evidence to investigate a reported flow.

These are initial assumptions and should be validated with users.

## Core workflow

1. A human requests an audit for a service and its cancellation entry point.
2. Before each run, a human reviews and approves that exact service and a registered dedicated test account, then explicitly starts the run.
3. The automated runner walks the flow through the service's normal user interface using only the approved test account.
4. The runner streams and records every meaningful observed action and resulting page or state.
5. Attach evidence to observations, such as a screenshot, visible text, or URL, while protecting personal information.
6. Stop before the final cancellation action, or stop earlier if the flow is blocked, the approved account cannot be verified, or it is unsafe to continue.
7. Produce a report that links each finding to the relevant observations and evidence.

## Report contents

- Service name, audit date, starting point, and audit outcome.
- An ordered timeline of observed steps, actions, and results.
- Evidence links for the observations used by each finding.
- Friction observations with a plain-language explanation of their effect on the user.
- Possible CCPA dark-pattern signals, stated as candidates for review rather than legal conclusions.
- Limitations, including where the journey stopped and any unavailable or inconclusive evidence.

## Product principles

- **Evidence first:** A finding must point to the steps and evidence that support it.
- **Describe before classifying:** Separate direct observations from interpretations and candidate legal signals.
- **Safe stopping boundary:** Never take the final action that cancels a subscription. Stop before it and record that the boundary was reached.
- **Human approval before every run:** A human must approve the service and its registered dedicated test account, then start the run. Approval is a required gate, not an optional review.
- **Dedicated test accounts only:** Never use a real personal account. Do not start if a dedicated test account cannot be approved and verified.
- **Visible automation:** Stream each observed step so the supervising human can follow the runner's progress.
- **User privacy:** Avoid collecting credentials and payment details. Minimize, redact, and protect personal data in captured evidence.
- **Reproducibility:** Preserve timestamps, page locations, and ordered actions so another reviewer can understand the path.
- **Honest uncertainty:** Mark inaccessible, ambiguous, or incomplete flows clearly; do not infer unseen behavior.

## Initial scope

- Audits of online subscription cancellation journeys used in India.
- Automated flow walking supervised by a human, with human approval of the service and test account before every run.
- Use of registered dedicated test accounts only; real personal accounts are never used.
- Recording ordered steps and evidence.
- Describing user-facing friction.
- Flagging possible CCPA dark-pattern signals for human review.
- Producing a report with evidence links, limitations, and a clear stop reason.

## Out of scope for the initial version

- Completing, scheduling, or submitting a cancellation.
- Running an audit without explicit human approval of the service and dedicated test account.
- Using a real personal account for an audit.
- Making a legal determination that a service violated a law or rule.
- Automatically contacting a provider, filing a complaint, or changing an account.
- Auditing flows that require bypassing access controls or defeating anti-abuse protections.
- Collecting or storing passwords, payment card data, or other secrets as audit evidence.

## Success measures to validate

- A reviewer can follow the report from a finding back to the exact supporting steps and evidence.
- Audits stop at the pre-cancellation boundary and make that stop visible in the report.
- Every run records the human approval of its service and dedicated test account before it starts.
- No run uses a real personal account; the runner verifies its account matches the approved dedicated test account.
- A supervising human can follow the live stream of observed steps.
- Independent reviewers can distinguish observations from candidate signals and conclusions.
- A user can understand why the flow was difficult without relying on unsupported claims.

## Open decisions

- Which subscription services and entry points are supported first?
- What evidence types are required, and how are screenshots redacted before storage?
- What are the data retention, deletion, and sharing defaults for audit evidence?
- Which candidate-signal taxonomy and legal review process should reports use?
- Who is the first target user, and what report format best serves them?
- How are dedicated test accounts registered, verified, and securely provisioned to the runner?
