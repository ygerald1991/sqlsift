"""Tests for sqlsift.filter module."""

import pytest
from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.filter import FilterCriteria, filter_results, top_slowest


def _make_result(
    query: str = "SELECT 1",
    duration_ms: float = 100.0,
    is_slow: bool = False,
    suggestions: list | None = None,
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


class TestFilterResults:
    def test_no_criteria_returns_all(self):
        results = [_make_result(), _make_result()]
        assert filter_results(results, FilterCriteria()) == results

    def test_min_duration_excludes_fast(self):
        results = [_make_result(duration_ms=50), _make_result(duration_ms=200)]
        out = filter_results(results, FilterCriteria(min_duration_ms=100))
        assert len(out) == 1
        assert out[0].entry.duration_ms == 200

    def test_max_duration_excludes_slow(self):
        results = [_make_result(duration_ms=50), _make_result(duration_ms=500)]
        out = filter_results(results, FilterCriteria(max_duration_ms=100))
        assert len(out) == 1
        assert out[0].entry.duration_ms == 50

    def test_only_slow_filters_fast(self):
        results = [
            _make_result(is_slow=False),
            _make_result(is_slow=True),
        ]
        out = filter_results(results, FilterCriteria(only_slow=True))
        assert len(out) == 1
        assert out[0].is_slow is True

    def test_only_with_suggestions(self):
        results = [
            _make_result(suggestions=[]),
            _make_result(suggestions=["Add index"]),
        ]
        out = filter_results(results, FilterCriteria(only_with_suggestions=True))
        assert len(out) == 1
        assert out[0].suggestions == ["Add index"]

    def test_query_contains_case_insensitive(self):
        results = [
            _make_result(query="SELECT * FROM users"),
            _make_result(query="SELECT id FROM orders"),
        ]
        out = filter_results(results, FilterCriteria(query_contains="USERS"))
        assert len(out) == 1
        assert "users" in out[0].entry.query.lower()

    def test_combined_criteria(self):
        results = [
            _make_result(query="SELECT * FROM users", duration_ms=300, is_slow=True),
            _make_result(query="SELECT id FROM orders", duration_ms=50, is_slow=False),
            _make_result(query="SELECT * FROM users", duration_ms=20, is_slow=False),
        ]
        criteria = FilterCriteria(min_duration_ms=100, query_contains="users")
        out = filter_results(results, criteria)
        assert len(out) == 1
        assert out[0].entry.duration_ms == 300

    def test_empty_input_returns_empty(self):
        assert filter_results([], FilterCriteria(only_slow=True)) == []


class TestTopSlowest:
    def test_returns_n_slowest(self):
        results = [
            _make_result(duration_ms=d)
            for d in [100, 500, 200, 800, 50]
        ]
        top = top_slowest(results, n=3)
        assert [r.entry.duration_ms for r in top] == [800, 500, 200]

    def test_fewer_than_n_returns_all(self):
        results = [_make_result(duration_ms=d) for d in [10, 20]]
        top = top_slowest(results, n=5)
        assert len(top) == 2

    def test_default_n_is_ten(self):
        results = [_make_result(duration_ms=float(i)) for i in range(20)]
        top = top_slowest(results)
        assert len(top) == 10

    def test_ordered_descending(self):
        results = [_make_result(duration_ms=d) for d in [30, 10, 20]]
        top = top_slowest(results, n=3)
        durations = [r.entry.duration_ms for r in top]
        assert durations == sorted(durations, reverse=True)
