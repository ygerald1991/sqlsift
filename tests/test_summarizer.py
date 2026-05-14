"""Tests for sqlsift.summarizer."""

import pytest
from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.reporter import Report
from sqlsift.scorer import ScoredResult, Severity
from sqlsift.summarizer import RunSummary, build_summary, format_summary


def _make_entry(duration_ms: float) -> QueryEntry:
    return QueryEntry(
        timestamp="2024-01-01T00:00:00",
        duration_ms=duration_ms,
        query="SELECT * FROM t",
    )


def _make_result(duration_ms: float, suggestions=None) -> AnalysisResult:
    return AnalysisResult(
        entry=_make_entry(duration_ms),
        is_slow=duration_ms >= 1000,
        suggestions=suggestions or [],
    )


def _make_scored(duration_ms: float, suggestions=None, severity=Severity.INFO) -> ScoredResult:
    result = _make_result(duration_ms, suggestions)
    return ScoredResult(result=result, score=0.0, severity=severity)


def _make_report(total: int, slow_count: int) -> Report:
    return Report(
        total=total,
        slow_count=slow_count,
        suggestions_by_query={},
    )


class TestBuildSummary:
    def test_empty_scored_gives_zero_durations(self):
        report = _make_report(0, 0)
        summary = build_summary(report, [])
        assert summary.avg_duration_ms == 0.0
        assert summary.max_duration_ms == 0.0

    def test_total_and_slow_counts_from_report(self):
        report = _make_report(10, 3)
        summary = build_summary(report, [])
        assert summary.total_queries == 10
        assert summary.slow_queries == 3

    def test_slow_ratio_calculated(self):
        report = _make_report(4, 1)
        summary = build_summary(report, [])
        assert summary.slow_ratio == pytest.approx(0.25)

    def test_avg_and_max_duration(self):
        scored = [
            _make_scored(100.0),
            _make_scored(300.0),
        ]
        summary = build_summary(_make_report(2, 0), scored)
        assert summary.avg_duration_ms == pytest.approx(200.0)
        assert summary.max_duration_ms == pytest.approx(300.0)

    def test_severity_counts(self):
        scored = [
            _make_scored(100, severity=Severity.CRITICAL),
            _make_scored(200, severity=Severity.WARNING),
            _make_scored(300, severity=Severity.WARNING),
            _make_scored(400, severity=Severity.INFO),
        ]
        summary = build_summary(_make_report(4, 0), scored)
        assert summary.critical_count == 1
        assert summary.warning_count == 2
        assert summary.info_count == 1

    def test_top_suggestions_ordered_by_frequency(self):
        scored = [
            _make_scored(100, suggestions=["Add index", "Avoid SELECT *"]),
            _make_scored(200, suggestions=["Add index"]),
            _make_scored(300, suggestions=["Add index", "Use LIMIT"]),
        ]
        summary = build_summary(_make_report(3, 0), scored)
        assert summary.top_suggestions[0] == "Add index"

    def test_top_suggestions_capped_at_three(self):
        scored = [
            _make_scored(100, suggestions=[f"Tip {i}" for i in range(6)]),
        ]
        summary = build_summary(_make_report(1, 0), scored)
        assert len(summary.top_suggestions) <= 3

    def test_no_suggestions_returns_empty_list(self):
        summary = build_summary(_make_report(1, 0), [_make_scored(100)])
        assert summary.top_suggestions == []


class TestFormatSummary:
    def test_output_contains_header(self):
        summary = RunSummary(0, 0, 0.0, 0.0, 0.0, 0, 0, 0, [])
        text = format_summary(summary)
        assert "SQLSift Run Summary" in text

    def test_output_contains_counts(self):
        summary = RunSummary(10, 3, 0.3, 150.0, 900.0, 1, 2, 0, ["Add index"])
        text = format_summary(summary)
        assert "10" in text
        assert "3" in text
        assert "Add index" in text

    def test_no_suggestions_label(self):
        summary = RunSummary(1, 0, 0.0, 50.0, 50.0, 0, 0, 1, [])
        text = format_summary(summary)
        assert "none" in text
