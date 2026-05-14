"""Tests for sqlsift.recommender."""

import pytest
from sqlsift.recommender import (
    build_recommendations,
    format_recommendations,
    Recommendation,
    RecommendationReport,
)
from sqlsift.scorer import ScoredResult, Severity
from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry


def _make_scored(query: str, duration: float, suggestions: list, severity: Severity, score: float) -> ScoredResult:
    entry = QueryEntry(timestamp="2024-01-01T00:00:00", duration=duration, query=query)
    result = AnalysisResult(entry=entry, is_slow=duration >= 1000, suggestions=suggestions)
    return ScoredResult(result=result, score=score, severity=severity)


class TestBuildRecommendations:
    def test_empty_input_returns_empty_report(self):
        report = build_recommendations([])
        assert report.total == 0
        assert report.recommendations == []

    def test_result_without_suggestions_excluded(self):
        sr = _make_scored("SELECT 1", 500.0, [], Severity.LOW, 10.0)
        report = build_recommendations([sr])
        assert report.total == 0

    def test_result_with_suggestions_included(self):
        sr = _make_scored("SELECT * FROM t", 2000.0, ["Avoid SELECT *"], Severity.HIGH, 70.0)
        report = build_recommendations([sr])
        assert report.total == 1
        assert report.recommendations[0].query == "SELECT * FROM t"

    def test_critical_count_tracked(self):
        sr1 = _make_scored("SELECT * FROM a", 5000.0, ["hint"], Severity.CRITICAL, 95.0)
        sr2 = _make_scored("SELECT * FROM b", 2000.0, ["hint"], Severity.HIGH, 70.0)
        report = build_recommendations([sr1, sr2])
        assert report.critical_count == 1
        assert report.high_count == 1

    def test_sorted_by_priority_then_score_descending(self):
        low = _make_scored("SELECT a", 100.0, ["x"], Severity.LOW, 20.0)
        critical = _make_scored("SELECT b", 9000.0, ["y"], Severity.CRITICAL, 95.0)
        high = _make_scored("SELECT c", 3000.0, ["z"], Severity.HIGH, 75.0)
        report = build_recommendations([low, high, critical])
        severities = [r.severity for r in report.recommendations]
        assert severities[0] == Severity.CRITICAL
        assert severities[1] == Severity.HIGH
        assert severities[2] == Severity.LOW

    def test_suggestions_preserved(self):
        hints = ["Add index", "Avoid SELECT *"]
        sr = _make_scored("SELECT * FROM t", 2000.0, hints, Severity.HIGH, 70.0)
        report = build_recommendations([sr])
        assert report.recommendations[0].suggestions == hints

    def test_priority_field_set_correctly(self):
        sr = _make_scored("SELECT 1", 5000.0, ["hint"], Severity.CRITICAL, 90.0)
        report = build_recommendations([sr])
        assert report.recommendations[0].priority == 1


class TestFormatRecommendations:
    def test_empty_report_shows_no_recommendations(self):
        report = RecommendationReport()
        output = format_recommendations(report)
        assert "No actionable recommendations" in output

    def test_output_contains_severity(self):
        sr = _make_scored("SELECT * FROM t", 3000.0, ["Add index"], Severity.HIGH, 75.0)
        report = build_recommendations([sr])
        output = format_recommendations(report)
        assert "HIGH" in output

    def test_output_contains_suggestion(self):
        sr = _make_scored("SELECT * FROM t", 3000.0, ["Add index on col"], Severity.HIGH, 75.0)
        report = build_recommendations([sr])
        output = format_recommendations(report)
        assert "Add index on col" in output

    def test_max_results_limits_output(self):
        scored = [
            _make_scored(f"SELECT {i} FROM t", 2000.0, ["hint"], Severity.MEDIUM, 50.0)
            for i in range(10)
        ]
        report = build_recommendations(scored)
        output = format_recommendations(report, max_results=3)
        assert output.count("• hint") == 3

    def test_long_query_truncated_in_output(self):
        long_query = "SELECT " + "col, " * 30 + "col FROM table"
        sr = _make_scored(long_query, 2000.0, ["hint"], Severity.HIGH, 70.0)
        report = build_recommendations([sr])
        output = format_recommendations(report)
        assert "..." in output
