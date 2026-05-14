"""Query profiler: tracks execution counts and timing statistics per normalized pattern."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from sqlsift.aggregator import normalize_pattern
from sqlsift.analyzer import AnalysisResult


@dataclass
class ProfileEntry:
    pattern: str
    executions: int = 0
    total_duration: float = 0.0
    min_duration: float = float("inf")
    max_duration: float = 0.0
    slow_count: int = 0
    all_suggestions: List[str] = field(default_factory=list)

    @property
    def avg_duration(self) -> float:
        if self.executions == 0:
            return 0.0
        return self.total_duration / self.executions

    @property
    def unique_suggestions(self) -> List[str]:
        return list(dict.fromkeys(self.all_suggestions))

    @property
    def slow_ratio(self) -> float:
        if self.executions == 0:
            return 0.0
        return self.slow_count / self.executions


def profile_results(results: List[AnalysisResult]) -> Dict[str, ProfileEntry]:
    """Aggregate AnalysisResult objects into per-pattern ProfileEntry records."""
    profiles: Dict[str, ProfileEntry] = {}

    for result in results:
        pattern = normalize_pattern(result.entry.query)
        if pattern not in profiles:
            profiles[pattern] = ProfileEntry(pattern=pattern)

        entry = profiles[pattern]
        duration = result.entry.duration

        entry.executions += 1
        entry.total_duration += duration
        entry.min_duration = min(entry.min_duration, duration)
        entry.max_duration = max(entry.max_duration, duration)

        if result.is_slow:
            entry.slow_count += 1

        entry.all_suggestions.extend(result.suggestions)

    return profiles


def top_patterns_by_total_time(
    profiles: Dict[str, ProfileEntry], n: int = 5
) -> List[ProfileEntry]:
    """Return the top-n patterns ranked by total cumulative duration."""
    sorted_entries = sorted(
        profiles.values(), key=lambda e: e.total_duration, reverse=True
    )
    return sorted_entries[:n]
