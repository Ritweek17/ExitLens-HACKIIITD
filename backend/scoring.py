"""Box D Evidence & Scoring Engine (documented in docs/api-contract.md).

Max indicator weights (total max = 100):
  - extra_steps:     up to 30  (Graduated: min(30, max(0, total_steps - 2) * 5))
  - hidden_cancel:   20        (Buried or visually de-emphasized cancel control)
  - redirects:       15        (Misdirection, loops, or dead-end navigation)
  - forced_reason:   15        (Mandatory survey / reason selection before proceeding)
  - retention_offer: 10        (Discount / pause walls interrupting cancellation)
  - unclear_copy:    10        (Confirm-shaming, guilt messaging, or confusing labels)

Rules:
  1. Evidence gate: A signal is `verified = True` ONLY if it references at least one
     valid Evidence item (with non-empty `content` or `url`). Missing evidence ->
     `verified = False` and `weight = 0`.
  2. Graduated extra_steps: Baseline fair exit is 2 steps. Each additional step adds
     5 points up to the 30-point cap (e.g. 5 steps = 15, 6 steps = 20, 7 steps = 25, 8+ steps = 30).
  3. Deduplication: Each indicator category can contribute its weight at most once per run.
     Subsequent signals in the same indicator category remain in the report for transparency
     but receive `weight = 0`.
  4. Exact sum: `friction_score` is the exact sum of `signal.weight` across all signals
     (never hardcoded).
"""

from models import Evidence, FrictionIndicator, FrictionSignal, Severity

BASELINE_STEPS = 2
EXTRA_STEP_UNIT_WEIGHT = 5
MAX_EXTRA_STEPS_WEIGHT = 30

INDICATOR_WEIGHTS: dict[FrictionIndicator, int] = {
    "extra_steps": MAX_EXTRA_STEPS_WEIGHT,
    "hidden_cancel": 20,
    "redirects": 15,
    "forced_reason": 15,
    "retention_offer": 10,
    "unclear_copy": 10,
}

INDICATOR_SEVERITY: dict[FrictionIndicator, Severity] = {
    "extra_steps": "high",
    "hidden_cancel": "high",
    "redirects": "medium",
    "forced_reason": "medium",
    "retention_offer": "low",
    "unclear_copy": "medium",
}


def compute_extra_steps_weight(total_steps: int) -> tuple[int, Severity]:
    """Return graduated weight (0..30) and severity for the observed step count."""
    extra = max(0, total_steps - BASELINE_STEPS)
    weight = min(MAX_EXTRA_STEPS_WEIGHT, extra * EXTRA_STEP_UNIT_WEIGHT)
    if weight >= 25:
        sev: Severity = "high"
    elif weight >= 15:
        sev = "medium"
    else:
        sev = "low"
    return weight, sev


def has_valid_evidence(signal: FrictionSignal, evidence_by_id: dict[str, Evidence]) -> bool:
    """Return True iff the signal links to at least one non-empty evidence record."""
    if not signal.evidence_ids:
        return False
    for ev_id in signal.evidence_ids:
        ev = evidence_by_id.get(ev_id)
        if ev is not None and (
            (ev.content and ev.content.strip()) or (ev.url and ev.url.strip())
        ):
            return True
    return False


def score_signals(
    signals: list[FrictionSignal],
    evidence: list[Evidence],
    total_steps: int | None = None,
) -> tuple[int, list[FrictionSignal]]:
    """Evaluate verification and deduplicated weights for each signal.

    Mutates and returns `(total_score, updated_signals)` so that:
      total_score == sum(s.weight for s in updated_signals)
    """
    evidence_by_id = {ev.id: ev for ev in evidence}
    seen_indicators: set[FrictionIndicator] = set()
    total_score = 0

    for sig in signals:
        verified = has_valid_evidence(sig, evidence_by_id)
        sig.verified = verified
        if verified and sig.indicator not in seen_indicators:
            seen_indicators.add(sig.indicator)
            if sig.indicator == "extra_steps":
                inferred_steps = (
                    total_steps
                    if total_steps is not None
                    else (max(sig.step_refs) if sig.step_refs else len(sig.step_refs))
                )
                # If no explicit step count > baseline was provided, default to full cap (30)
                if inferred_steps <= BASELINE_STEPS:
                    sig.weight = MAX_EXTRA_STEPS_WEIGHT
                else:
                    sig.weight, sig.severity = compute_extra_steps_weight(inferred_steps)
            else:
                sig.weight = INDICATOR_WEIGHTS[sig.indicator]
            total_score += sig.weight
        else:
            sig.weight = 0

    return min(100, total_score), signals
