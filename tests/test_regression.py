"""Tests for sqlsift.regression."""

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.baseline import Baseline, BaselineEntry, build_baseline
from sqlsift.parser import QueryEntry
from sqlsift.regression import RegressionReport, detect_regressions


def _make_result(query: str, duration: float, suggestions=None, is_slow=True):
    entry = QueryEntry(timestamp="2024-01-01T00:00:00", duration=duration, query=query)
    return AnalysisResult(
        entry=entry,
        is_slow=is_slow,
        suggestions=suggestions or [],
    )


def _make_baseline(*entries: BaselineEntry) -> Baseline:
    return Baseline(entries={e.query: e for e in entries})


class TestDetectRegressions:
    def test_empty_results_returns_empty_report(self):
        report = detect_regressions([], Baseline())
        assert report.count == 0

    def test_fast_query_not_flagged(self):
        r = _make_result("SELECT 1", 0.5, is_slow=False)
        report = detect_regressions([r], Baseline())
        assert report.count == 0

    def test_new_slow_query_flagged_as_new(self):
        r = _make_result("SELECT 1", 2.0, is_slow=True)
        report = detect_regressions([r], Baseline())
        assert report.count == 1
        assert report.regressions[0].is_new is True
        assert report.regressions[0].baseline_duration is None

    def test_query_within_threshold_not_flagged(self):
        baseline = _make_baseline(
            BaselineEntry(query="SELECT 1", avg_duration=2.0, suggestion_count=1, occurrences=1)
        )
        r = _make_result("SELECT 1", 2.1, ["idx"], is_slow=True)  # 5% increase
        report = detect_regressions([r], baseline, duration_threshold=0.10)
        assert report.count == 0

    def test_query_exceeding_threshold_flagged(self):
        baseline = _make_baseline(
            BaselineEntry(query="SELECT 1", avg_duration=2.0, suggestion_count=1, occurrences=1)
        )
        r = _make_result("SELECT 1", 2.5, ["idx"], is_slow=True)  # 25% increase
        report = detect_regressions([r], baseline, duration_threshold=0.10)
        assert report.count == 1
        item = report.regressions[0]
        assert item.is_new is False
        assert item.duration_delta == pytest.approx(0.5)
        assert item.baseline_duration == pytest.approx(2.0)

    def test_new_suggestion_triggers_regression(self):
        baseline = _make_baseline(
            BaselineEntry(query="SELECT 1", avg_duration=2.0, suggestion_count=1, occurrences=1)
        )
        r = _make_result("SELECT 1", 2.0, ["a", "b"], is_slow=True)  # same duration, +1 suggestion
        report = detect_regressions([r], baseline)
        assert report.count == 1

    def test_report_new_queries_property(self):
        r = _make_result("SELECT 1", 2.0, is_slow=True)
        report = detect_regressions([r], Baseline())
        assert len(report.new_queries) == 1
        assert len(report.worsened_queries) == 0

    def test_report_worsened_queries_property(self):
        baseline = _make_baseline(
            BaselineEntry(query="SELECT 1", avg_duration=1.0, suggestion_count=0, occurrences=1)
        )
        r = _make_result("SELECT 1", 3.0, is_slow=True)
        report = detect_regressions([r], baseline)
        assert len(report.worsened_queries) == 1
        assert len(report.new_queries) == 0

    def test_multiple_results_mixed_outcomes(self):
        baseline = _make_baseline(
            BaselineEntry(query="SELECT 1", avg_duration=1.0, suggestion_count=0, occurrences=1)
        )
        results = [
            _make_result("SELECT 1", 1.05, is_slow=True),  # within threshold
            _make_result("SELECT 2", 5.0, is_slow=True),   # new
        ]
        report = detect_regressions(results, baseline)
        assert report.count == 1
        assert report.regressions[0].query == "SELECT 2"
