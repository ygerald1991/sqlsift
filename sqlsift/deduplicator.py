"""Deduplication utilities for collapsing repeated query results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from sqlsift.analyzer import AnalysisResult
from sqlsift.aggregator import normalize_pattern


@dataclass
class DeduplicatedGroup:
    """A group of results that share the same normalized query pattern."""

    pattern: str
    results: List[AnalysisResult] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.results)

    @property
    def avg_duration(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.entry.duration for r in self.results) / len(self.results)

    @property
    def max_duration(self) -> float:
        if not self.results:
            return 0.0
        return max(r.entry.duration for r in self.results)

    @property
    def all_suggestions(self) -> List[str]:
        """Unique suggestions across all results in the group."""
        seen: set = set()
        unique: List[str] = []
        for result in self.results:
            for suggestion in result.suggestions:
                if suggestion not in seen:
                    seen.add(suggestion)
                    unique.append(suggestion)
        return unique


def deduplicate(
    results: List[AnalysisResult],
) -> Dict[str, DeduplicatedGroup]:
    """Group results by normalized query pattern.

    Args:
        results: List of AnalysisResult objects to deduplicate.

    Returns:
        Mapping from normalized pattern to DeduplicatedGroup.
    """
    groups: Dict[str, DeduplicatedGroup] = {}
    for result in results:
        pattern = normalize_pattern(result.entry.query)
        if pattern not in groups:
            groups[pattern] = DeduplicatedGroup(pattern=pattern)
        groups[pattern].results.append(result)
    return groups


def top_duplicate_patterns(
    results: List[AnalysisResult], limit: int = 5
) -> List[DeduplicatedGroup]:
    """Return the most frequently repeated query patterns.

    Args:
        results: List of AnalysisResult objects.
        limit: Maximum number of groups to return.

    Returns:
        List of DeduplicatedGroup sorted by occurrence count descending.
    """
    groups = deduplicate(results)
    sorted_groups = sorted(groups.values(), key=lambda g: g.count, reverse=True)
    return sorted_groups[:limit]
