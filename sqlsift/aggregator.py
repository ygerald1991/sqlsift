"""Aggregator module for grouping and summarizing analysis results."""

from dataclasses import dataclass, field
from collections import defaultdict
from typing import Dict, List, Optional
from sqlsift.analyzer import AnalysisResult


@dataclass
class QueryGroup:
    """A group of results sharing the same query pattern."""
    pattern: str
    results: List[AnalysisResult] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.results)

    @property
    def avg_duration(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.duration_ms for r in self.results) / len(self.results)

    @property
    def max_duration(self) -> float:
        if not self.results:
            return 0.0
        return max(r.duration_ms for r in self.results)

    @property
    def total_duration(self) -> float:
        return sum(r.duration_ms for r in self.results)

    @property
    def slow_count(self) -> int:
        return sum(1 for r in self.results if r.is_slow)


@dataclass
class AggregationSummary:
    """Summary statistics across all query groups."""
    total_queries: int
    total_slow: int
    unique_patterns: int
    groups: List[QueryGroup]

    @property
    def slow_ratio(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return self.total_slow / self.total_queries


def _normalize_pattern(query: str) -> str:
    """Normalize a SQL query to a pattern by stripping extra whitespace."""
    import re
    normalized = re.sub(r'\s+', ' ', query.strip().upper())
    normalized = re.sub(r'\b\d+\b', '?', normalized)
    normalized = re.sub(r"'[^']*'", '?', normalized)
    return normalized


def group_by_pattern(results: List[AnalysisResult]) -> Dict[str, QueryGroup]:
    """Group results by normalized query pattern."""
    groups: Dict[str, QueryGroup] = {}
    for result in results:
        pattern = _normalize_pattern(result.query)
        if pattern not in groups:
            groups[pattern] = QueryGroup(pattern=pattern)
        groups[pattern].results.append(result)
    return groups


def aggregate(results: List[AnalysisResult]) -> AggregationSummary:
    """Aggregate a list of analysis results into a summary."""
    groups = group_by_pattern(results)
    group_list = sorted(groups.values(), key=lambda g: g.total_duration, reverse=True)
    total_slow = sum(1 for r in results if r.is_slow)
    return AggregationSummary(
        total_queries=len(results),
        total_slow=total_slow,
        unique_patterns=len(groups),
        groups=group_list,
    )
