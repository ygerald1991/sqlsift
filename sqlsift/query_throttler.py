"""query_throttler.py – rate-limit / throttle detection for repeated slow queries.

Identifies queries that appear too frequently within a rolling time window and
flags them as candidates for caching or application-level throttling.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlsift.query_fingerprint import _normalize  # reuse existing normaliser


@dataclass
class ThrottleEntry:
    """Aggregated view of a single query pattern within the analysis window."""

    pattern: str
    occurrences: int
    total_duration_ms: float
    flagged: bool  # True when occurrences exceed the threshold

    @property
    def avg_duration_ms(self) -> float:
        if self.occurrences == 0:
            return 0.0
        return self.total_duration_ms / self.occurrences


@dataclass
class ThrottleReport:
    """Collection of throttle entries produced by :func:`build_throttle_report`."""

    entries: List[ThrottleEntry] = field(default_factory=list)
    threshold: int = 10

    @property
    def count(self) -> int:
        return len(self.entries)

    @property
    def flagged(self) -> List[ThrottleEntry]:
        return [e for e in self.entries if e.flagged]


def _pattern(query: str) -> str:
    """Return a normalised fingerprint for *query*."""
    return _normalize(query)


def build_throttle_report(
    results: List,  # List[AnalysisResult] – avoid circular import
    threshold: int = 10,
) -> ThrottleReport:
    """Build a :class:`ThrottleReport` from *results*.

    A query pattern is *flagged* when it appears at least *threshold* times
    across the supplied results.

    Parameters
    ----------
    results:
        Iterable of ``AnalysisResult`` objects (as produced by
        :func:`sqlsift.analyzer.analyze_entries`).
    threshold:
        Minimum occurrence count to flag a pattern.  Defaults to ``10``.
    """
    counts: Dict[str, int] = {}
    durations: Dict[str, float] = {}

    for r in results:
        key = _pattern(r.entry.query)
        counts[key] = counts.get(key, 0) + 1
        durations[key] = durations.get(key, 0.0) + r.entry.duration_ms

    entries = [
        ThrottleEntry(
            pattern=key,
            occurrences=cnt,
            total_duration_ms=durations[key],
            flagged=cnt >= threshold,
        )
        for key, cnt in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    ]

    return ThrottleReport(entries=entries, threshold=threshold)
