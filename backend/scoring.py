"""Friction score: a simple, explainable formula (documented in docs/api-contract.md).

score = min(100, extra_steps * 5 + sum(severity weights))
  extra_steps = steps taken to reach the final cancel button beyond a 2-step baseline
  severity weights: low = 5, medium = 10, high = 20
"""

from models import FrictionSignal

BASELINE_STEPS = 2
STEP_WEIGHT = 5
SEVERITY_WEIGHTS = {"low": 5, "medium": 10, "high": 20}


def compute_friction_score(steps_to_boundary: int, signals: list[FrictionSignal]) -> int:
    extra_steps = max(0, steps_to_boundary - BASELINE_STEPS)
    score = extra_steps * STEP_WEIGHT + sum(SEVERITY_WEIGHTS[s.severity] for s in signals)
    return min(100, score)
