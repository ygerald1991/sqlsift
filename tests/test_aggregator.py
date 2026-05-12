"""Tests for sqlsift.aggregator module."""

import pytest
from sqlsift.aggregator import (
    QueryGroup,
    AggregationSummary,
    _normalize_pattern,
    group_by_pattern,
    aggregate,
)
from sqlsift.analyzer import AnalysisResult


def _make_result(query: str, duration_ms: float, is_slow: bool = False) -> AnalysisResult:
    return AnalysisResult(
        query=query,
        duration_ms=duration_ms,
        is_slow=is_slow,
        suggestions=["Use index"] if is_slow else [],
    )


class TestNormalizePattern:
    def test_whitespace_collapsed(self):
        assert _normalize_pattern("SELECT  *  FROM  users") == "SELECT * FROM USERS"

    def test_numeric_literals_replaced(self):
        result = _normalize_pattern("SELECT * FROM users WHERE id = 42")
        assert "?" in result
        assert "42" not in result

    def test_string_literals_replaced(self):
        result = _normalize_pattern("SELECT * FROM users WHERE name = 'Alice'")
        assert "?" in result
        assert "Alice" not in result

    def test_uppercase_normalization(self):
        result = _normalize_pattern("select * from users")
        assert result == result.upper()


class TestGroupByPattern:
    def test_identical_queries_grouped(self):
        results = [
            _make_result("SELECT * FROM users", 100),
            _make_result("SELECT * FROM users", 200),
        ]
        groups = group_by_pattern(results)
        assert len(groups) == 1
        group = list(groups.values())[0]
        assert group.count == 2

    def test_different_queries_separate_groups(self):
        results = [
            _make_result("SELECT * FROM users", 100),
            _make_result("SELECT * FROM orders", 200),
        ]
        groups = group_by_pattern(results)
        assert len(groups) == 2

    def test_empty_results_returns_empty_dict(self):
        assert group_by_pattern([]) == {}


class TestQueryGroup:
    def test_avg_duration(self):
        group = QueryGroup(pattern="SELECT * FROM USERS")
        group.results = [_make_result("SELECT * FROM users", 100), _make_result("SELECT * FROM users", 300)]
        assert group.avg_duration == 200.0

    def test_max_duration(self):
        group = QueryGroup(pattern="SELECT * FROM USERS")
        group.results = [_make_result("SELECT * FROM users", 50), _make_result("SELECT * FROM users", 500)]
        assert group.max_duration == 500.0

    def test_slow_count(self):
        group = QueryGroup(pattern="SELECT * FROM USERS")
        group.results = [
            _make_result("SELECT * FROM users", 50, is_slow=False),
            _make_result("SELECT * FROM users", 500, is_slow=True),
        ]
        assert group.slow_count == 1

    def test_empty_group_defaults(self):
        group = QueryGroup(pattern="EMPTY")
        assert group.avg_duration == 0.0
        assert group.max_duration == 0.0
        assert group.count == 0


class TestAggregate:
    def test_aggregate_counts(self):
        results = [
            _make_result("SELECT * FROM users", 100, is_slow=False),
            _make_result("SELECT * FROM users", 600, is_slow=True),
            _make_result("SELECT * FROM orders", 800, is_slow=True),
        ]
        summary = aggregate(results)
        assert summary.total_queries == 3
        assert summary.total_slow == 2
        assert summary.unique_patterns == 2

    def test_aggregate_slow_ratio(self):
        results = [
            _make_result("SELECT * FROM users", 100, is_slow=False),
            _make_result("SELECT * FROM orders", 800, is_slow=True),
        ]
        summary = aggregate(results)
        assert summary.slow_ratio == pytest.approx(0.5)

    def test_aggregate_empty(self):
        summary = aggregate([])
        assert summary.total_queries == 0
        assert summary.slow_ratio == 0.0
        assert summary.unique_patterns == 0

    def test_groups_sorted_by_total_duration(self):
        results = [
            _make_result("SELECT * FROM users", 50),
            _make_result("SELECT * FROM orders", 900),
        ]
        summary = aggregate(results)
        assert summary.groups[0].total_duration >= summary.groups[1].total_duration
