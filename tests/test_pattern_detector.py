"""Tests for sqlsift.pattern_detector."""

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.pattern_detector import (
    PatternFinding,
    PatternReport,
    build_pattern_report,
    detect_patterns,
)


def _make_result(query: str, duration: float = 1.5, is_slow: bool = True) -> AnalysisResult:
    entry = QueryEntry(
        timestamp="2024-01-01T00:00:00",
        duration=duration,
        query=query,
        table=None,
    )
    return AnalysisResult(entry=entry, is_slow=is_slow, suggestions=[])


class TestDetectPatterns:
    def test_select_star_detected(self):
        result = _make_result("SELECT * FROM users")
        findings = detect_patterns(result)
        ids = [f.pattern_id for f in findings]
        assert "select_star" in ids

    def test_leading_wildcard_detected(self):
        result = _make_result("SELECT id FROM users WHERE name LIKE '%smith'")
        findings = detect_patterns(result)
        ids = [f.pattern_id for f in findings]
        assert "leading_wildcard" in ids

    def test_or_in_where_detected(self):
        result = _make_result("SELECT id FROM t WHERE a=1 OR b=2")
        findings = detect_patterns(result)
        ids = [f.pattern_id for f in findings]
        assert "or_in_where" in ids

    def test_not_in_detected(self):
        result = _make_result("SELECT id FROM t WHERE id NOT IN (1,2,3)")
        findings = detect_patterns(result)
        ids = [f.pattern_id for f in findings]
        assert "not_in" in ids

    def test_clean_query_no_findings(self):
        result = _make_result("SELECT id, name FROM users WHERE id = 1 LIMIT 10")
        findings = detect_patterns(result)
        assert findings == []

    def test_finding_carries_original_query(self):
        query = "SELECT * FROM orders"
        result = _make_result(query)
        findings = detect_patterns(result)
        assert all(f.query == query for f in findings)

    def test_select_star_severity_is_medium(self):
        result = _make_result("SELECT * FROM orders")
        findings = detect_patterns(result)
        star = next(f for f in findings if f.pattern_id == "select_star")
        assert star.severity == "medium"

    def test_leading_wildcard_severity_is_high(self):
        result = _make_result("SELECT id FROM t WHERE name LIKE '%x'")
        findings = detect_patterns(result)
        wc = next(f for f in findings if f.pattern_id == "leading_wildcard")
        assert wc.severity == "high"


class TestBuildPatternReport:
    def test_empty_input_returns_empty_report(self):
        report = build_pattern_report([])
        assert isinstance(report, PatternReport)
        assert report.count == 0

    def test_count_aggregates_across_results(self):
        r1 = _make_result("SELECT * FROM a")
        r2 = _make_result("SELECT id FROM b WHERE name LIKE '%z'")
        report = build_pattern_report([r1, r2])
        assert report.count >= 2

    def test_by_severity_filters_correctly(self):
        r1 = _make_result("SELECT * FROM a WHERE name LIKE '%x'")
        report = build_pattern_report([r1])
        high = report.by_severity("high")
        assert all(f.severity == "high" for f in high)

    def test_by_severity_unknown_returns_empty(self):
        report = build_pattern_report([])
        assert report.by_severity("critical") == []
