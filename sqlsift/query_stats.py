"""Compute per-query statistical summaries from analysis results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence
import statistics

from sqlsift.analyzer import AnalysisResult


@dataclass
class QueryStats:
    query: str
    count: int
    min_duration: float
    max_duration: float
    mean_duration: float
    median_duration: float
    stdev_duration: float
    slow_count: int
    suggestion_counts: List[int] = field(default_factory=list)

    @property
    def slow_ratio(self) -> float:
        return self.slow_count / self.count if self.count else 0.0

    @property
    def avg_suggestions(self) -> float:
        return sum(self.suggestion_counts) / len(self.suggestion_counts) if self.suggestion_counts else 0.0


def _key(result: AnalysisResult) -> str:
    return result.entry.query.strip().lower()


def compute_stats(results: Sequence[AnalysisResult]) -> Dict[str, QueryStats]:
    """Group results by query text and compute statistical summaries."""
    buckets: Dict[str, List[AnalysisResult]] = {}
    for r in results:
        k = _key(r)
        buckets.setdefault(k, []).append(r)

    stats: Dict[str, QueryStats] = {}
    for query, group in buckets.items():
        durations = [r.entry.duration for r in group]
        slow_count = sum(1 for r in group if r.is_slow)
        suggestion_counts = [len(r.suggestions) for r in group]
        stdev = statistics.stdev(durations) if len(durations) > 1 else 0.0
        stats[query] = QueryStats(
            query=group[0].entry.query,
            count=len(group),
            min_duration=min(durations),
            max_duration=max(durations),
            mean_duration=statistics.mean(durations),
            median_duration=statistics.median(durations),
            stdev_duration=stdev,
            slow_count=slow_count,
            suggestion_counts=suggestion_counts,
        )
    return stats
