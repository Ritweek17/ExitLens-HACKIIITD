"""Box D Evidence & Scoring Engine (documented in docs/api-contract.md).

Weights (total max = 100):
  - extra_steps:     30  (Excessive clicks/navigation depth to reach cancellation)
  - hidden_cancel:   20  (Buried or visually de-emphasized cancel control)
  - redirects:       15  (Misdirection, loops, or dead-end navigation)
  - forced_reason:   15  (Mandatory survey / reason selection before proceeding)
  - retention_offer: 10  (Discount / pause walls interrupting cancellation)
  - unclear_copy:    10  (Confirm-shaming, guilt messaging, or confusing labels)

Rules:
  1. Evidence gate: A signal is `verified = True` ONLY if it references at least one
     valid Evidence item (with non-empty `content` or `url`). Missing evidence ->
     `verified = False` and `weight = 0`.
  2. Deduplication: Each indicator category can contribute its weight at most once per run.
     Subsequent signals in the same indicator category remain in the report for transparency
     but receive `weight = 0`.
  3. Exact sum: `friction_score` is the exact sum of `signal.weight` across all signals
     (never hardcoded).
"""

from models import Evidence, FrictionIndicator, FrictionSignal

INDICATOR_WEIGHTS: dict[FrictionIndicator, int] = {
    "extra_steps": 30,
    "hidden_cancel": 20,
    "redirects": 15,
    "forced_reason": 15,
    "retention_offer": 10,
    "unclear_copy": 10,
}

INDICATOR_SEVERITY: dict[FrictionIndicator, str] = {
    "extra_steps": "high",
    "hidden_cancel": "high",
    "redirects": "medium",
    "forced_reason": "medium",
    "retention_offer": "low",
    "unclear_copy": "medium",
}


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
            sig.weight = INDICATOR_WEIGHTS[sig.indicator]
            total_score += sig.weight
        else:
            sig.weight = 0

    return min(100, total_score), signals
