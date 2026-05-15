"""Tests for sqlsift.grouper."""

from __future__ import annotations

from sqlsift.analyzer import AnalysisResult
from sqlsift.grouper import GroupBy, ResultGroup, group_results
from sqlsift.parser import QueryEntry


def _make_result(
    query: str,
    duration: float = 100.0,
    is_slow: bool = False,
    timestamp: str = "2024-01-15 10:30:00",
) -> AnalysisResult:
    entry = QueryEntry(query=query, duration=duration, timestamp=timestamp)
    return AnalysisResult(entry=entry, is_slow=is_slow, suggestions=[])


class TestGroupResults:
    def test_empty_input_returns_empty_dict(self):
        assert group_results([]) == {}

    def test_group_by_operation_select(self):
        r = _make_result("SELECT * FROM users")
        groups = group_results([r], by=GroupBy.OPERATION)
        assert "SELECT" in groups
        assert groups["SELECT"].count == 1

    def test_group_by_operation_multiple(self):
        results = [
            _make_result("SELECT id FROM orders"),
            _make_result("INSERT INTO logs VALUES (1)"),
            _make_result("SELECT name FROM users"),
        ]
        groups = group_results(results, by=GroupBy.OPERATION)
        assert groups["SELECT"].count == 2
        assert groups["INSERT"].count == 1

    def test_group_by_table_from_clause(self):
        results = [
            _make_result("SELECT * FROM orders WHERE id = 1"),
            _make_result("SELECT * FROM orders WHERE id = 2"),
            _make_result("SELECT * FROM users"),
        ]
        groups = group_results(results, by=GroupBy.TABLE)
        assert groups["ORDERS"].count == 2
        assert groups["USERS"].count == 1

    def test_group_by_table_update(self):
        r = _make_result("UPDATE products SET price = 10 WHERE id = 5")
        groups = group_results([r], by=GroupBy.TABLE)
        assert "PRODUCTS" in groups

    def test_group_by_table_unknown_fallback(self):
        r = _make_result("SHOW TABLES")
        groups = group_results([r], by=GroupBy.TABLE)
        assert "UNKNOWN" in groups

    def test_group_by_hour(self):
        results = [
            _make_result("SELECT 1", timestamp="2024-01-15 10:00:00"),
            _make_result("SELECT 2", timestamp="2024-01-15 10:45:00"),
            _make_result("SELECT 3", timestamp="2024-01-15 11:05:00"),
        ]
        groups = group_results(results, by=GroupBy.HOUR)
        assert groups["2024-01-15 10"].count == 2
        assert groups["2024-01-15 11"].count == 1

    def test_group_by_hour_no_timestamp(self):
        r = _make_result("SELECT 1", timestamp="")
        groups = group_results([r], by=GroupBy.HOUR)
        assert "UNKNOWN" in groups

    def test_result_group_avg_duration(self):
        results = [
            _make_result("SELECT 1", duration=200.0),
            _make_result("SELECT 2", duration=400.0),
        ]
        groups = group_results(results, by=GroupBy.OPERATION)
        assert groups["SELECT"].avg_duration == 300.0

    def test_result_group_slow_count(self):
        results = [
            _make_result("SELECT 1", is_slow=True),
            _make_result("SELECT 2", is_slow=False),
            _make_result("SELECT 3", is_slow=True),
        ]
        groups = group_results(results, by=GroupBy.OPERATION)
        assert groups["SELECT"].slow_count == 2

    def test_result_group_slow_ratio(self):
        results = [
            _make_result("SELECT 1", is_slow=True),
            _make_result("SELECT 2", is_slow=False),
        ]
        groups = group_results(results, by=GroupBy.OPERATION)
        assert groups["SELECT"].slow_ratio == 0.5

    def test_empty_group_avg_duration_is_zero(self):
        g = ResultGroup(key="empty")
        assert g.avg_duration == 0.0
        assert g.slow_ratio == 0.0
