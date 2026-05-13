"""Query severity scoring module for sqlsift."""

from dataclasses import dataclass
from enum import Enum
from typing import List

from sqlsift.analyzer import AnalysisResult


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ScoredResult:
    result: AnalysisResult
    score: int
    severity: Severity


# Weights used to compute the composite score
_DURATION_WEIGHT = 0.6
_SUGGESTION_WEIGHT = 0.4
_DURATION_SCALE = 5000.0  # ms considered "very slow"
_MAX_SUGGESTIONS = 5


def compute_score(result: AnalysisResult) -> int:
    """Return an integer score in [0, 100] representing query badness."""
    duration_component = min(result.duration_ms / _DURATION_SCALE, 1.0)
    suggestion_count = len(result.suggestions)
    suggestion_component = min(suggestion_count / _MAX_SUGGESTIONS, 1.0)
    raw = (_DURATION_WEIGHT * duration_component + _SUGGESTION_WEIGHT * suggestion_component)
    return round(raw * 100)


def classify_severity(score: int) -> Severity:
    """Map a numeric score to a Severity level."""
    if score >= 80:
        return Severity.CRITICAL
    if score >= 50:
        return Severity.HIGH
    if score >= 25:
        return Severity.MEDIUM
    return Severity.LOW


def score_result(result: AnalysisResult) -> ScoredResult:
    """Attach a score and severity to a single AnalysisResult."""
    score = compute_score(result)
    severity = classify_severity(score)
    return ScoredResult(result=result, score=score, severity=severity)


def score_results(results: List[AnalysisResult]) -> List[ScoredResult]:
    """Score and sort a list of AnalysisResult objects, highest score first."""
    scored = [score_result(r) for r in results]
    return sorted(scored, key=lambda s: s.score, reverse=True)
