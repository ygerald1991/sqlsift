"""Estimate relative query cost based on analysis results and patterns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from sqlsift.analyzer import AnalysisResult
from sqlsift.scorer import ScoredResult, Severity

# Weights used to compute a composite cost estimate (0–100 scale)
_DURATION_WEIGHT = 0.5
_SUGGESTION_WEIGHT = 0.3
_SEVERITY_WEIGHT = 0.2

_SEVERITY_SCORES: dict[Severity, float] = {
    Severity.LOW: 0.0,
    Severity.MEDIUM: 33.0,
    Severity.HIGH: 66.0,
    Severity.CRITICAL: 100.0,
}

_MAX_DURATION_MS = 30_000.0
_MAX_SUGGESTIONS = 5


@dataclass(frozen=True)
class CostEstimate:
    query: str
    duration_ms: float
    suggestion_count: int
    severity: Severity
    cost_score: float  # 0.0 – 100.0
    breakdown: dict[str, float] = field(default_factory=dict)


def _duration_component(duration_ms: float) -> float:
    clamped = min(duration_ms, _MAX_DURATION_MS)
    return (clamped / _MAX_DURATION_MS) * 100.0


def _suggestion_component(suggestion_count: int) -> float:
    clamped = min(suggestion_count, _MAX_SUGGESTIONS)
    return (clamped / _MAX_SUGGESTIONS) * 100.0


def _severity_component(severity: Severity) -> float:
    return _SEVERITY_SCORES.get(severity, 0.0)


def estimate_cost(scored: ScoredResult) -> CostEstimate:
    """Compute a cost estimate for a single scored result."""
    result: AnalysisResult = scored.result
    dur = _duration_component(result.entry.duration_ms)
    sug = _suggestion_component(len(result.suggestions))
    sev = _severity_component(scored.severity)

    cost = (
        _DURATION_WEIGHT * dur
        + _SUGGESTION_WEIGHT * sug
        + _SEVERITY_WEIGHT * sev
    )

    breakdown = {
        "duration": round(dur, 2),
        "suggestions": round(sug, 2),
        "severity": round(sev, 2),
    }

    return CostEstimate(
        query=result.entry.query,
        duration_ms=result.entry.duration_ms,
        suggestion_count=len(result.suggestions),
        severity=scored.severity,
        cost_score=round(cost, 2),
        breakdown=breakdown,
    )


def estimate_costs(scored_results: List[ScoredResult]) -> List[CostEstimate]:
    """Return cost estimates sorted by cost_score descending."""
    estimates = [estimate_cost(s) for s in scored_results]
    return sorted(estimates, key=lambda e: e.cost_score, reverse=True)
