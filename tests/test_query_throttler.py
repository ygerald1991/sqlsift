"""Tests for sqlsift.query_throttler and sqlsift.throttle_formatter."""
from __future__ import annotations

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.query_throttler import (
    ThrottleEntry,
    ThrottleReport,
    build_throttle_report,
)
from sqlsift.throttle_formatter import format_throttle_entry, format_throttle_report


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_result(query: str, duration_ms: float = 500.0) -> AnalysisResult:
    entry = QueryEntry(
        timestamp=None,
        duration_ms=duration_ms,
        query=query,
        user=None,
        host=None,
    )
    return AnalysisResult(entry=entry, is_slow=duration_ms >= 500, suggestions=[])


# ---------------------------------------------------------------------------
# ThrottleEntry
# ---------------------------------------------------------------------------

class TestThrottleEntry:
    def test_avg_duration_zero_occurrences(self):
        e = ThrottleEntry(pattern="SELECT 1", occurrences=0,
                          total_duration_ms=0.0, flagged=False)
        assert e.avg_duration_ms == 0.0

    def test_avg_duration_calculated(self):
        e = ThrottleEntry(pattern="SELECT 1", occurrences=4,
                          total_duration_ms=200.0, flagged=False)
        assert e.avg_duration_ms == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# build_throttle_report
# ---------------------------------------------------------------------------

class TestBuildThrottleReport:
    def test_empty_input_returns_empty_report(self):
        report = build_throttle_report([])
        assert report.count == 0
        assert report.flagged == []

    def test_single_result_creates_one_entry(self):
        results = [_make_result("SELECT id FROM users")]
        report = build_throttle_report(results, threshold=2)
        assert report.count == 1
        assert report.entries[0].occurrences == 1

    def test_identical_queries_grouped(self):
        results = [_make_result("SELECT id FROM users")] * 5
        report = build_throttle_report(results, threshold=3)
        assert report.count == 1
        assert report.entries[0].occurrences == 5

    def test_flagged_when_at_threshold(self):
        results = [_make_result("SELECT 1")] * 10
        report = build_throttle_report(results, threshold=10)
        assert report.entries[0].flagged is True

    def test_not_flagged_below_threshold(self):
        results = [_make_result("SELECT 1")] * 3
        report = build_throttle_report(results, threshold=10)
        assert report.entries[0].flagged is False

    def test_multiple_patterns_separated(self):
        results = (
            [_make_result("SELECT a FROM t")] * 6
            + [_make_result("SELECT b FROM t")] * 2
        )
        report = build_throttle_report(results, threshold=5)
        assert report.count == 2
        flagged_patterns = [e.pattern for e in report.flagged]
        assert len(flagged_patterns) == 1

    def test_entries_sorted_by_occurrence_descending(self):
        results = (
            [_make_result("SELECT a FROM t")] * 2
            + [_make_result("SELECT b FROM t")] * 7
        )
        report = build_throttle_report(results, threshold=100)
        assert report.entries[0].occurrences >= report.entries[1].occurrences

    def test_total_duration_accumulated(self):
        results = [_make_result("SELECT 1", duration_ms=100.0)] * 3
        report = build_throttle_report(results, threshold=10)
        assert report.entries[0].total_duration_ms == pytest.approx(300.0)

    def test_threshold_stored_on_report(self):
        report = build_throttle_report([], threshold=42)
        assert report.threshold == 42


# ---------------------------------------------------------------------------
# format_throttle_report
# ---------------------------------------------------------------------------

class TestFormatThrottleReport:
    def test_returns_string(self):
        report = build_throttle_report([])
        assert isinstance(format_throttle_report(report), str)

    def test_empty_report_contains_no_data(self):
        report = build_throttle_report([])
        text = format_throttle_report(report)
        assert "(no data)" in text

    def test_flagged_label_present(self):
        results = [_make_result("SELECT 1")] * 15
        report = build_throttle_report(results, threshold=5)
        text = format_throttle_report(report)
        assert "[FLAGGED]" in text

    def test_ok_label_present_for_low_occurrence(self):
        results = [_make_result("SELECT 1")] * 2
        report = build_throttle_report(results, threshold=10)
        text = format_throttle_report(report)
        assert "[ok]" in text

    def test_format_entry_includes_occurrences(self):
        entry = ThrottleEntry(
            pattern="SELECT id FROM users",
            occurrences=7,
            total_duration_ms=700.0,
            flagged=False,
        )
        line = format_throttle_entry(entry)
        assert "7" in line
