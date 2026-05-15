"""Tests for sqlsift.pattern_formatter."""

import pytest

from sqlsift.pattern_detector import PatternFinding, PatternReport
from sqlsift.pattern_formatter import (
    _truncate,
    format_finding,
    format_pattern_report,
)


def _make_finding(
    pattern_id: str = "select_star",
    description: str = "Use explicit columns",
    severity: str = "medium",
    query: str = "SELECT * FROM t",
) -> PatternFinding:
    return PatternFinding(
        pattern_id=pattern_id,
        description=description,
        severity=severity,
        query=query,
    )


class TestTruncate:
    def test_short_string_unchanged(self):
        assert _truncate("short") == "short"

    def test_long_string_truncated(self):
        long = "x" * 100
        result = _truncate(long)
        assert len(result) == 80
        assert result.endswith("...")

    def test_exactly_max_len_unchanged(self):
        s = "a" * 80
        assert _truncate(s) == s


class TestFormatFinding:
    def test_contains_severity_tag(self):
        f = _make_finding(severity="high")
        assert "[HIGH]" in format_finding(f)

    def test_contains_pattern_id(self):
        f = _make_finding(pattern_id="leading_wildcard")
        assert "leading_wildcard" in format_finding(f)

    def test_contains_description(self):
        f = _make_finding(description="Some description")
        assert "Some description" in format_finding(f)

    def test_long_query_truncated_in_output(self):
        long_query = "SELECT " + "a, " * 40 + "b FROM t"
        f = _make_finding(query=long_query)
        line = format_finding(f)
        assert "..." in line


class TestFormatPatternReport:
    def test_empty_report_returns_no_findings_message(self):
        report = PatternReport()
        output = format_pattern_report(report)
        assert "No anti-patterns" in output

    def test_report_header_present(self):
        report = PatternReport(findings=[_make_finding()])
        output = format_pattern_report(report)
        assert "Pattern Report" in output

    def test_count_in_header(self):
        findings = [_make_finding(), _make_finding(pattern_id="not_in")]
        report = PatternReport(findings=findings)
        output = format_pattern_report(report)
        assert "2" in output

    def test_summary_line_present(self):
        report = PatternReport(findings=[_make_finding(severity="high")])
        output = format_pattern_report(report)
        assert "Summary:" in output
        assert "high=1" in output

    def test_high_severity_appears_before_low(self):
        findings = [
            _make_finding(pattern_id="low_pat", severity="low"),
            _make_finding(pattern_id="high_pat", severity="high"),
        ]
        report = PatternReport(findings=findings)
        output = format_pattern_report(report)
        assert output.index("high_pat") < output.index("low_pat")
