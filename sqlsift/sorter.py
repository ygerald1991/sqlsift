"""Sorting utilities for analysis results."""

from enum import Enum
from typing import List

from sqlsift.analyzer import AnalysisResult


class SortKey(str, Enum):
    DURATION = "duration"
    SUGGESTION_COUNT = "suggestion_count"
    QUERY = "query"
    TIMESTAMP = "timestamp"


def sort_results(
    results: List[AnalysisResult],
    key: SortKey = SortKey.DURATION,
    descending: bool = True,
) -> List[AnalysisResult]:
    """Return a sorted copy of *results* by the given *key*."""
    key_funcs = {
        SortKey.DURATION: lambda r: r.entry.duration_ms,
        SortKey.SUGGESTION_COUNT: lambda r: len(r.suggestions),
        SortKey.QUERY: lambda r: r.entry.query.lower(),
        SortKey.TIMESTAMP: lambda r: r.entry.timestamp or "",
    }
    return sorted(results, key=key_funcs[key], reverse=descending)
