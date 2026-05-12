"""Filtering utilities for query analysis results."""

from dataclasses import dataclass
from typing import List, Optional

from sqlsift.analyzer import AnalysisResult


@dataclass
class FilterCriteria:
    """Criteria used to filter analysis results."""
    min_duration_ms: Optional[float] = None
    max_duration_ms: Optional[float] = None
    only_slow: bool = False
    only_with_suggestions: bool = False
    query_contains: Optional[str] = None


def filter_results(
    results: List[AnalysisResult],
    criteria: FilterCriteria,
) -> List[AnalysisResult]:
    """Return results matching all provided filter criteria."""
    filtered = results

    if criteria.min_duration_ms is not None:
        filtered = [
            r for r in filtered
            if r.entry.duration_ms >= criteria.min_duration_ms
        ]

    if criteria.max_duration_ms is not None:
        filtered = [
            r for r in filtered
            if r.entry.duration_ms <= criteria.max_duration_ms
        ]

    if criteria.only_slow:
        filtered = [r for r in filtered if r.is_slow]

    if criteria.only_with_suggestions:
        filtered = [r for r in filtered if r.suggestions]

    if criteria.query_contains:
        needle = criteria.query_contains.lower()
        filtered = [
            r for r in filtered
            if needle in r.entry.query.lower()
        ]

    return filtered


def top_slowest(
    results: List[AnalysisResult],
    n: int = 10,
) -> List[AnalysisResult]:
    """Return the *n* slowest results ordered by duration descending."""
    return sorted(results, key=lambda r: r.entry.duration_ms, reverse=True)[:n]
