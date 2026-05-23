"""Tests for sqlsift.query_stats."""
from __future__ import annotations

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.query_stats import QueryStats, compute_stats


def _make_result(
    query: str = "SELECT 1",
    duration: float = 100.0,
    is_slow: bool = False,
    suggestions: list[str] | None = None,
) -> AnalysisResult:
    entry = QueryEntry(timestamp="2024-01-01T00:00:00", query=query, duration=duration)
    return AnalysisResult(
        entry=entry,
        is_slow=is_slow,
        suggestions=suggestions or [],
    )


class TestComputeStats:
    def test_empty_input_returns_empty_dict(self):
        assert compute_stats([]) == {}

    def test_single_result_creates_one_entry(self):
        result = _make_result(query="SELECT 1", duration=200.0)
        stats = compute_stats([result])
        assert len(stats) == 1

    def test_key_is_normalised_query(self):
        r1 = _make_result(query="SELECT 1", duration=100.0)
        r2 = _make_result(query="select 1", duration=200.0)
        stats = compute_stats([r1, r2])
        assert len(stats) == 1

    def test_count_reflects_group_size(self):
        results = [_make_result(query="SELECT a", duration=float(d)) for d in range(1, 6)]
        stats = compute_stats(results)
        entry = next(iter(stats.values()))
        assert entry.count == 5

    def test_min_max_duration(self):
        results = [_make_result(duration=d) for d in [50.0, 150.0, 300.0]]
        entry = next(iter(compute_stats(results).values()))
        assert entry.min_duration == 50.0
        assert entry.max_duration == 300.0

    def test_mean_duration(self):
        results = [_make_result(duration=d) for d in [100.0, 200.0, 300.0]]
        entry = next(iter(compute_stats(results).values()))
        assert entry.mean_duration == pytest.approx(200.0)

    def test_median_duration(self):
        results = [_make_result(duration=d) for d in [100.0, 200.0, 900.0]]
        entry = next(iter(compute_stats(results).values()))
        assert entry.median_duration == pytest.approx(200.0)

    def test_stdev_single_result_is_zero(self):
        entry = next(iter(compute_stats([_make_result(duration=100.0)]).values()))
        assert entry.stdev_duration == 0.0

    def test_stdev_multiple_results(self):
        import statistics
        durations = [100.0, 200.0, 300.0]
        results = [_make_result(duration=d) for d in durations]
        entry = next(iter(compute_stats(results).values()))
        assert entry.stdev_duration == pytest.approx(statistics.stdev(durations))

    def test_slow_count(self):
        results = [
            _make_result(is_slow=True),
            _make_result(is_slow=False),
            _make_result(is_slow=True),
        ]
        entry = next(iter(compute_stats(results).values()))
        assert entry.slow_count == 2

    def test_slow_ratio(self):
        results = [_make_result(is_slow=i < 3) for i in range(6)]
        entry = next(iter(compute_stats(results).values()))
        assert entry.slow_ratio == pytest.approx(0.5)

    def test_avg_suggestions(self):
        results = [
            _make_result(suggestions=["add index"]),
            _make_result(suggestions=["avoid select *", "add index"]),
            _make_result(suggestions=[]),
        ]
        entry = next(iter(compute_stats(results).values()))
        assert entry.avg_suggestions == pytest.approx(1.0)

    def test_multiple_distinct_queries(self):
        r1 = _make_result(query="SELECT a", duration=100.0)
        r2 = _make_result(query="SELECT b", duration=200.0)
        stats = compute_stats([r1, r2])
        assert len(stats) == 2
