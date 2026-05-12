"""Analyzer module for detecting slow queries and generating optimization hints."""

from dataclasses import dataclass, field
from typing import List, Optional
from .parser import QueryEntry


DEFAULT_SLOW_THRESHOLD_MS = 1000.0

SUSPECT_PATTERNS = [
    ("SELECT *", "Avoid SELECT *; specify only the columns you need."),
    ("LIKE '%", "Leading wildcard in LIKE prevents index usage; consider full-text search."),
    ("NOT IN", "NOT IN can be slow on large sets; consider NOT EXISTS or a LEFT JOIN."),
    ("OR ", "OR conditions may prevent index usage; consider UNION or separate queries."),
    ("ORDER BY RAND()", "ORDER BY RAND() is very slow on large tables; use an alternative sampling strategy."),
]


@dataclass
class AnalysisResult:
    entry: QueryEntry
    is_slow: bool
    duration_ms: float
    suggestions: List[str] = field(default_factory=list)

    def has_suggestions(self) -> bool:
        return len(self.suggestions) > 0


def _extract_suggestions(sql: str) -> List[str]:
    """Return optimization hints based on simple pattern matching."""
    hints: List[str] = []
    upper_sql = sql.upper()
    for pattern, hint in SUSPECT_PATTERNS:
        if pattern.upper() in upper_sql:
            hints.append(hint)
    return hints


def analyze_entry(
    entry: QueryEntry,
    slow_threshold_ms: float = DEFAULT_SLOW_THRESHOLD_MS,
) -> AnalysisResult:
    """Analyze a single QueryEntry and return an AnalysisResult."""
    duration_ms = entry.duration_ms if entry.duration_ms is not None else 0.0
    slow = duration_ms >= slow_threshold_ms
    suggestions = _extract_suggestions(entry.query)
    return AnalysisResult(
        entry=entry,
        is_slow=slow,
        duration_ms=duration_ms,
        suggestions=suggestions,
    )


def analyze_entries(
    entries: List[QueryEntry],
    slow_threshold_ms: float = DEFAULT_SLOW_THRESHOLD_MS,
    only_slow: bool = False,
) -> List[AnalysisResult]:
    """Analyze a list of QueryEntry objects.

    Args:
        entries: Parsed query entries.
        slow_threshold_ms: Threshold in milliseconds to classify a query as slow.
        only_slow: If True, return only results for slow queries.

    Returns:
        List of AnalysisResult objects.
    """
    results = [analyze_entry(e, slow_threshold_ms) for e in entries]
    if only_slow:
        results = [r for r in results if r.is_slow]
    return results
