"""Tests for sqlsift.cost_formatter."""

from __future__ import annotations

from sqlsift.analyzer import AnalysisResult
from sqlsift.cost_estimator import CostEstimate, estimate_cost
from sqlsift.cost_formatter import (
    _bar,
    _truncate,
    format_estimate,
    format_cost_report,
)
from sqlsift.parser import QueryEntry
from sqlsift.scorer import Severity, ScoredResult


def _make_estimate(
    query: str = "SELECT 1",
    duration_ms: float = 500.0,
    suggestions: list[str] | None = None,
    severity: Severity = Severity.LOW,
    score: float = 10.0,
) -> CostEstimate:
    entry = QueryEntry(timestamp="2024-01-01T00:00:00", duration_ms=duration_ms, query=query)
    result = AnalysisResult(entry=entry, suggestions=suggestions or [])
    scored = ScoredResult(result=result, score=score, severity=severity)
    return estimate_cost(scored)


class TestTruncate:
    def test_short_string_unchanged(self):
        assert _truncate("SELECT 1") == "SELECT 1"

    def test_long_string_truncated(self):
        long = "A" * 80
        result = _truncate(long)
        assert len(result) <= 60
        assert result.endswith("...")

    def test_exactly_max_len_unchanged(self):
        s = "B" * 60
        assert _truncate(s) == s


class TestBar:
    def test_zero_score_all_dashes(self):
        b = _bar(0.0, width=10)
        assert b == "[" + "-" * 10 + "]"

    def test_full_score_all_hashes(self):
        b = _bar(100.0, width=10)
        assert b == "[" + "#" * 10 + "]"

    def test_half_score_half_filled(self):
        b = _bar(50.0, width=10)
        assert b.count("#") == 5
        assert b.count("-") == 5


class TestFormatEstimate:
    def test_returns_string(self):
        est = _make_estimate()
        assert isinstance(format_estimate(est), str)

    def test_query_appears_in_output(self):
        est = _make_estimate(query="SELECT id FROM orders")
        output = format_estimate(est)
        assert "SELECT id FROM orders" in output

    def test_cost_score_appears_in_output(self):
        est = _make_estimate()
        output = format_estimate(est)
        assert str(est.cost_score) in output or f"{est.cost_score:.2f}" in output

    def test_severity_appears_in_output(self):
        est = _make_estimate(severity=Severity.HIGH)
        output = format_estimate(est)
        assert "HIGH" in output or "high" in output.lower()


class TestFormatCostReport:
    def test_empty_list_returns_fallback(self):
        output = format_cost_report([])
        assert "No cost estimates" in output

    def test_single_estimate_included(self):
        est = _make_estimate(query="SELECT * FROM logs")
        output = format_cost_report([est])
        assert "SELECT * FROM logs" in output

    def test_header_present(self):
        est = _make_estimate()
        output = format_cost_report([est])
        assert "COST REPORT" in output

    def test_total_queries_shown(self):
        estimates = [_make_estimate(), _make_estimate(query="SELECT 2")]
        output = format_cost_report(estimates)
        assert "Total queries: 2" in output

    def test_avg_cost_shown(self):
        estimates = [_make_estimate(), _make_estimate(query="SELECT 2")]
        output = format_cost_report(estimates)
        assert "Avg cost" in output
