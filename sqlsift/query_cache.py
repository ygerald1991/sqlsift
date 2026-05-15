"""Query result caching: track repeated queries and cache hit/miss stats."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlsift.analyzer import AnalysisResult


@dataclass
class CacheEntry:
    query: str
    hit_count: int = 0
    miss_count: int = 0
    last_duration_ms: float = 0.0
    suggestions: List[str] = field(default_factory=list)

    @property
    def total_calls(self) -> int:
        return self.hit_count + self.miss_count

    @property
    def hit_ratio(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.hit_count / self.total_calls


@dataclass
class CacheReport:
    entries: Dict[str, CacheEntry] = field(default_factory=dict)

    @property
    def total_queries(self) -> int:
        return sum(e.total_calls for e in self.entries.values())

    @property
    def total_hits(self) -> int:
        return sum(e.hit_count for e in self.entries.values())

    @property
    def total_misses(self) -> int:
        return sum(e.miss_count for e in self.entries.values())

    @property
    def overall_hit_ratio(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return self.total_hits / self.total_queries


_CACHE_HIT_HINTS = {"cache", "hit", "qcache"}


def _is_cache_hit(result: AnalysisResult) -> bool:
    """Heuristic: treat a result as a cache hit if its query mentions cache keywords
    or if it has no suggestions and duration is very low (<= 1 ms)."""
    q = result.entry.query.lower()
    if any(h in q for h in _CACHE_HIT_HINTS):
        return True
    if not result.suggestions and result.entry.duration_ms <= 1.0:
        return True
    return False


def build_cache_report(results: List[AnalysisResult]) -> CacheReport:
    """Aggregate results into a CacheReport keyed by normalised query text."""
    report = CacheReport()
    for r in results:
        key = r.entry.query.strip()
        if key not in report.entries:
            report.entries[key] = CacheEntry(
                query=key,
                suggestions=list(r.suggestions),
            )
        entry = report.entries[key]
        entry.last_duration_ms = r.entry.duration_ms
        if _is_cache_hit(r):
            entry.hit_count += 1
        else:
            entry.miss_count += 1
    return report
