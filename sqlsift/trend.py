"""Trend analysis: compare query performance across multiple runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlsift.baseline import Baseline


@dataclass
class TrendPoint:
    """A single data point in a query's performance trend."""

    run_id: str
    avg_duration: float
    slow_ratio: float
    sample_count: int


@dataclass
class TrendEntry:
    """Trend data for a single normalized query."""

    query: str
    points: List[TrendPoint] = field(default_factory=list)

    def is_improving(self) -> bool:
        """Return True if the latest duration is lower than the earliest."""
        if len(self.points) < 2:
            return False
        return self.points[-1].avg_duration < self.points[0].avg_duration

    def is_degrading(self) -> bool:
        """Return True if the latest duration is higher than the earliest."""
        if len(self.points) < 2:
            return False
        return self.points[-1].avg_duration > self.points[0].avg_duration

    def delta(self) -> Optional[float]:
        """Return change in avg_duration from first to last point, or None."""
        if len(self.points) < 2:
            return None
        return self.points[-1].avg_duration - self.points[0].avg_duration


@dataclass
class TrendReport:
    """Collection of trend entries across multiple baselines."""

    entries: Dict[str, TrendEntry] = field(default_factory=dict)

    def degrading(self) -> List[TrendEntry]:
        return [e for e in self.entries.values() if e.is_degrading()]

    def improving(self) -> List[TrendEntry]:
        return [e for e in self.entries.values() if e.is_improving()]


def build_trend(runs: List[tuple[str, Baseline]]) -> TrendReport:
    """Build a TrendReport from an ordered list of (run_id, Baseline) pairs."""
    report = TrendReport()
    for run_id, baseline in runs:
        for query, entry in baseline.entries.items():
            if query not in report.entries:
                report.entries[query] = TrendEntry(query=query)
            point = TrendPoint(
                run_id=run_id,
                avg_duration=entry.avg_duration,
                slow_ratio=entry.slow_ratio,
                sample_count=entry.sample_count,
            )
            report.entries[query].points.append(point)
    return report
