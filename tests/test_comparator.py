"""Tests for sqlsift.comparator."""

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.comparator import compare_results, ComparisonSummary


def _make_result(query: str, duration: float, is_slow: bool = False, suggestions=None) -> AnalysisResult:
    entry = QueryEntry(timestamp="2024-01-01T00:00:00", duration=duration, query=query)
    return AnalysisResult(
        entry=entry,
        is_slow=is_slow,
        suggestions=suggestions or [],
    )


class TestCompareResults:
    def test_empty_inputs_return_empty_summary(self):
        summary = compare_results([], [])
        assert summary.new_slow_queries == []
        assert summary.resolved_slow_queries == []
        assert summary.regressed == []
        assert summary.improved == []
        assert summary.unchanged == []

    def test_new_slow_query_detected(self):
        cur = _make_result("SELECT 1", duration=2.0, is_slow=True)
        summary = compare_results(baseline=[], current=[cur])
        assert len(summary.new_slow_queries) == 1
        assert summary.new_slow_queries[0].entry.query == "SELECT 1"

    def test_new_fast_query_not_flagged(self):
        cur = _make_result("SELECT 1", duration=0.05, is_slow=False)
        summary = compare_results(baseline=[], current=[cur])
        assert summary.new_slow_queries == []

    def test_resolved_slow_query_detected(self):
        base = _make_result("SELECT * FROM t", duration=3.0, is_slow=True)
        summary = compare_results(baseline=[base], current=[])
        assert len(summary.resolved_slow_queries) == 1
        assert summary.resolved_slow_queries[0].entry.query == "SELECT * FROM t"

    def test_regression_detected_above_threshold(self):
        base = _make_result("SELECT a FROM b", duration=0.5)
        cur = _make_result("SELECT a FROM b", duration=1.0)
        summary = compare_results([base], [cur], duration_threshold=0.1)
        assert len(summary.regressed) == 1
        b, c = summary.regressed[0]
        assert b.entry.duration == 0.5
        assert c.entry.duration == 1.0

    def test_improvement_detected_below_threshold(self):
        base = _make_result("SELECT a FROM b", duration=1.0)
        cur = _make_result("SELECT a FROM b", duration=0.3)
        summary = compare_results([base], [cur], duration_threshold=0.1)
        assert len(summary.improved) == 1

    def test_unchanged_within_threshold(self):
        base = _make_result("SELECT 1", duration=1.0)
        cur = _make_result("SELECT 1", duration=1.05)
        summary = compare_results([base], [cur], duration_threshold=0.1)
        assert len(summary.unchanged) == 1
        assert summary.regressed == []
        assert summary.improved == []

    def test_multiple_queries_classified_independently(self):
        baseline = [
            _make_result("SELECT a", duration=0.5),
            _make_result("SELECT b", duration=0.5),
        ]
        current = [
            _make_result("SELECT a", duration=1.0),   # regressed
            _make_result("SELECT b", duration=0.1),   # improved
            _make_result("SELECT c", duration=2.0, is_slow=True),  # new slow
        ]
        summary = compare_results(baseline, current, duration_threshold=0.1)
        assert len(summary.regressed) == 1
        assert len(summary.improved) == 1
        assert len(summary.new_slow_queries) == 1
        assert summary.resolved_slow_queries == []
