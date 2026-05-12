"""Tests for sqlsift.reporter module."""

import pytest
from sqlsift.parser import QueryEntry
from sqlsift.analyzer import AnalysisResult
from sqlsift.reporter import build_report, format_report, Report


def _make_result(
    query: str,
    duration_ms: float,
    is_slow: bool,
    suggestions: list = None,
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


class TestBuildReport:
    def test_empty_results_gives_zero_counts(self):
        report = build_report([])
        assert report.total_queries == 0
        assert report.slow_queries == 0
        assert report.entries_with_suggestions == 0
        assert report.suggestions_by_query == []

    def test_counts_slow_queries(self):
        results = [
            _make_result("SELECT 1", 50, False),
            _make_result("SELECT * FROM orders", 1500, True, ["Avoid SELECT *"]),
            _make_result("SELECT id FROM users", 2000, True, ["Add index"]),
        ]
        report = build_report(results)
        assert report.total_queries == 3
        assert report.slow_queries == 2
        assert report.entries_with_suggestions == 2

    def test_suggestions_by_query_content(self):
        results = [
            _make_result("SELECT * FROM t", 1200, True, ["Avoid SELECT *"]),
        ]
        report = build_report(results)
        assert len(report.suggestions_by_query) == 1
        item = report.suggestions_by_query[0]
        assert item["query"] == "SELECT * FROM t"
        assert item["duration_ms"] == 1200
        assert "Avoid SELECT *" in item["suggestions"]

    def test_slow_query_ratio(self):
        results = [
            _make_result("SELECT 1", 10, False),
            _make_result("SELECT 2", 10, False),
            _make_result("SELECT * FROM t", 2000, True),
        ]
        report = build_report(results)
        assert abs(report.slow_query_ratio - 1 / 3) < 1e-9

    def test_zero_total_ratio_is_zero(self):
        report = build_report([])
        assert report.slow_query_ratio == 0.0


class TestFormatReport:
    def _simple_report(self):
        return Report(
            total_queries=5,
            slow_queries=2,
            entries_with_suggestions=1,
            suggestions_by_query=[
                {
                    "query": "SELECT * FROM orders",
                    "duration_ms": 1500,
                    "suggestions": ["Avoid SELECT *"],
                }
            ],
        )

    def test_format_contains_header(self):
        output = format_report(self._simple_report())
        assert "SQLSift Report" in output

    def test_format_contains_counts(self):
        output = format_report(self._simple_report())
        assert "5" in output
        assert "2" in output

    def test_verbose_includes_suggestions(self):
        output = format_report(self._simple_report(), verbose=True)
        assert "Avoid SELECT *" in output
        assert "SELECT * FROM orders" in output

    def test_non_verbose_omits_suggestions(self):
        output = format_report(self._simple_report(), verbose=False)
        assert "Avoid SELECT *" not in output
