"""Tests for sqlsift.query_cache."""
from __future__ import annotations

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.query_cache import (
    CacheEntry,
    CacheReport,
    _is_cache_hit,
    build_cache_report,
)


def _make_result(
    query: str = "SELECT 1",
    duration_ms: float = 100.0,
    suggestions: list[str] | None = None,
    is_slow: bool = False,
) -> AnalysisResult:
    entry = QueryEntry(
        timestamp="2024-01-01T00:00:00",
        duration_ms=duration_ms,
        query=query,
    )
    return AnalysisResult(
        entry=entry,
        is_slow=is_slow,
        suggestions=suggestions or [],
    )


class TestIsCacheHit:
    def test_low_duration_no_suggestions_is_hit(self):
        r = _make_result(duration_ms=0.5, suggestions=[])
        assert _is_cache_hit(r) is True

    def test_low_duration_with_suggestions_is_not_hit(self):
        r = _make_result(duration_ms=0.5, suggestions=["Add index"])
        assert _is_cache_hit(r) is False

    def test_high_duration_no_suggestions_is_not_hit(self):
        r = _make_result(duration_ms=500.0, suggestions=[])
        assert _is_cache_hit(r) is False

    def test_query_with_cache_keyword_is_hit(self):
        r = _make_result(query="SELECT qcache_hits", duration_ms=200.0)
        assert _is_cache_hit(r) is True

    def test_exact_1ms_is_hit(self):
        r = _make_result(duration_ms=1.0, suggestions=[])
        assert _is_cache_hit(r) is True


class TestBuildCacheReport:
    def test_empty_input_returns_empty_report(self):
        report = build_cache_report([])
        assert isinstance(report, CacheReport)
        assert report.entries == {}
        assert report.total_queries == 0

    def test_single_miss_recorded(self):
        r = _make_result(duration_ms=300.0, suggestions=["Use index"])
        report = build_cache_report([r])
        assert len(report.entries) == 1
        entry = next(iter(report.entries.values()))
        assert entry.miss_count == 1
        assert entry.hit_count == 0

    def test_single_hit_recorded(self):
        r = _make_result(duration_ms=0.5)
        report = build_cache_report([r])
        entry = next(iter(report.entries.values()))
        assert entry.hit_count == 1
        assert entry.miss_count == 0

    def test_duplicate_queries_merged(self):
        r1 = _make_result(query="SELECT 1", duration_ms=0.5)
        r2 = _make_result(query="SELECT 1", duration_ms=200.0, suggestions=["idx"])
        report = build_cache_report([r1, r2])
        assert len(report.entries) == 1
        entry = report.entries["SELECT 1"]
        assert entry.total_calls == 2

    def test_hit_ratio_calculation(self):
        results = [
            _make_result(duration_ms=0.5),
            _make_result(duration_ms=0.5),
            _make_result(duration_ms=300.0, suggestions=["idx"]),
        ]
        report = build_cache_report(results)
        entry = next(iter(report.entries.values()))
        assert abs(entry.hit_ratio - 2 / 3) < 1e-9

    def test_overall_hit_ratio_across_queries(self):
        r1 = _make_result(query="SELECT 1", duration_ms=0.5)
        r2 = _make_result(query="SELECT 2", duration_ms=300.0, suggestions=["idx"])
        report = build_cache_report([r1, r2])
        assert report.total_hits == 1
        assert report.total_misses == 1
        assert abs(report.overall_hit_ratio - 0.5) < 1e-9

    def test_last_duration_updated(self):
        r1 = _make_result(query="SELECT 1", duration_ms=50.0, suggestions=["x"])
        r2 = _make_result(query="SELECT 1", duration_ms=99.0, suggestions=["x"])
        report = build_cache_report([r1, r2])
        assert report.entries["SELECT 1"].last_duration_ms == 99.0
