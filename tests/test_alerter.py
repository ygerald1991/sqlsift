"""Tests for sqlsift.alerter."""

from __future__ import annotations

from sqlsift.alerter import Alert, AlertReport, build_alerts, format_alerts, _extract_table
from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.scorer import ScoredResult, Severity
from sqlsift.threshold import ThresholdConfig


def _make_scored(
    query: str = "SELECT * FROM users",
    duration_ms: float = 200.0,
    suggestions: list[str] | None = None,
    severity: Severity = Severity.MEDIUM,
) -> ScoredResult:
    entry = QueryEntry(timestamp="2024-01-01T00:00:00", duration_ms=duration_ms, query=query)
    result = AnalysisResult(entry=entry, is_slow=duration_ms >= 100, suggestions=suggestions or [])
    return ScoredResult(result=result, score=50.0, severity=severity)


def _default_config(global_threshold: float = 100.0) -> ThresholdConfig:
    return ThresholdConfig(global_threshold_ms=global_threshold)


class TestExtractTable:
    def test_from_clause(self):
        assert _extract_table("SELECT * FROM orders") == "orders"

    def test_update_clause(self):
        assert _extract_table("UPDATE products SET price=1") == "products"

    def test_join_clause(self):
        assert _extract_table("SELECT * FROM a JOIN b ON a.id=b.id") == "a"

    def test_no_table_returns_none(self):
        assert _extract_table("SHOW TABLES") is None

    def test_into_clause(self):
        assert _extract_table("INSERT INTO logs VALUES (1)") == "logs"


class TestBuildAlerts:
    def test_empty_input_returns_empty_report(self):
        report = build_alerts([], _default_config())
        assert report.count == 0

    def test_fast_query_not_alerted(self):
        sr = _make_scored(duration_ms=50.0)
        report = build_alerts([sr], _default_config(global_threshold=100.0))
        assert report.count == 0

    def test_slow_query_creates_alert(self):
        sr = _make_scored(duration_ms=250.0)
        report = build_alerts([sr], _default_config(global_threshold=100.0))
        assert report.count == 1

    def test_alert_has_correct_duration(self):
        sr = _make_scored(duration_ms=300.0)
        report = build_alerts([sr], _default_config())
        assert report.alerts[0].duration_ms == 300.0

    def test_alert_preserves_severity(self):
        sr = _make_scored(duration_ms=500.0, severity=Severity.HIGH)
        report = build_alerts([sr], _default_config())
        assert report.alerts[0].severity == Severity.HIGH

    def test_alert_preserves_suggestions(self):
        sr = _make_scored(duration_ms=200.0, suggestions=["Add index"])
        report = build_alerts([sr], _default_config())
        assert "Add index" in report.alerts[0].suggestions

    def test_per_table_threshold_respected(self):
        config = ThresholdConfig(global_threshold_ms=100.0, per_table={"users": 500.0})
        sr = _make_scored(query="SELECT * FROM users", duration_ms=200.0)
        report = build_alerts([sr], config)
        assert report.count == 0

    def test_by_severity_filters_correctly(self):
        high = _make_scored(duration_ms=500.0, severity=Severity.HIGH)
        med = _make_scored(duration_ms=200.0, severity=Severity.MEDIUM)
        report = build_alerts([high, med], _default_config())
        assert len(report.by_severity(Severity.HIGH)) == 1
        assert len(report.by_severity(Severity.MEDIUM)) == 1


class TestFormatAlerts:
    def test_no_alerts_message(self):
        report = AlertReport()
        assert format_alerts(report) == "No alerts."

    def test_alert_message_contains_severity(self):
        sr = _make_scored(duration_ms=300.0, severity=Severity.HIGH)
        report = build_alerts([sr], _default_config())
        output = format_alerts(report)
        assert "HIGH" in output

    def test_alert_message_contains_query_snippet(self):
        sr = _make_scored(query="SELECT * FROM users", duration_ms=300.0)
        report = build_alerts([sr], _default_config())
        output = format_alerts(report)
        assert "SELECT" in output

    def test_suggestions_listed_in_output(self):
        sr = _make_scored(duration_ms=300.0, suggestions=["Use LIMIT"])
        report = build_alerts([sr], _default_config())
        output = format_alerts(report)
        assert "Use LIMIT" in output
