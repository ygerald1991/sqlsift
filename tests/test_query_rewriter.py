"""Tests for sqlsift.query_rewriter and sqlsift.rewriter_formatter."""
from __future__ import annotations

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.scorer import ScoredResult, Severity
from sqlsift.query_rewriter import (
    RewriteResult,
    RewriteSuggestion,
    rewrite_query,
    rewrite_queries,
)
from sqlsift.rewriter_formatter import (
    format_rewrite_result,
    format_rewrite_report,
    _truncate,
)


def _make_scored(query: str, severity: Severity = Severity.HIGH, duration: float = 2000.0) -> ScoredResult:
    entry = QueryEntry(timestamp=None, duration_ms=duration, query=query, table=None)
    result = AnalysisResult(entry=entry, is_slow=True, suggestions=["add index"])
    return ScoredResult(result=result, score=80.0, severity=severity)


# ---------------------------------------------------------------------------
# RewriteSuggestion
# ---------------------------------------------------------------------------

class TestRewriteSuggestion:
    def test_str_includes_reason_and_rewritten(self):
        s = RewriteSuggestion(original="SELECT * FROM t", rewritten="SELECT id FROM t", reason="explicit cols")
        assert "explicit cols" in str(s)
        assert "SELECT id FROM t" in str(s)


# ---------------------------------------------------------------------------
# rewrite_query
# ---------------------------------------------------------------------------

class TestRewriteQuery:
    def test_low_severity_returns_no_suggestions(self):
        scored = _make_scored("SELECT * FROM t", severity=Severity.LOW)
        result = rewrite_query(scored)
        assert isinstance(result, RewriteResult)
        assert not result.has_suggestions

    def test_medium_severity_returns_no_suggestions(self):
        scored = _make_scored("SELECT * FROM t", severity=Severity.MEDIUM)
        result = rewrite_query(scored)
        assert not result.has_suggestions

    def test_select_star_detected_on_high_severity(self):
        scored = _make_scored("SELECT * FROM orders", severity=Severity.HIGH)
        result = rewrite_query(scored)
        assert result.has_suggestions
        reasons = [s.reason for s in result.suggestions]
        assert any("SELECT *" in r for r in reasons)

    def test_or_in_where_detected(self):
        scored = _make_scored("SELECT id FROM t WHERE a=1 OR b=2", severity=Severity.HIGH)
        result = rewrite_query(scored)
        reasons = [s.reason for s in result.suggestions]
        assert any("OR" in r for r in reasons)

    def test_not_in_detected(self):
        scored = _make_scored("SELECT id FROM t WHERE id NOT IN (1,2,3)", severity=Severity.CRITICAL)
        result = rewrite_query(scored)
        reasons = [s.reason for s in result.suggestions]
        assert any("NOT IN" in r for r in reasons)

    def test_clean_query_no_suggestions(self):
        scored = _make_scored("SELECT id, name FROM users WHERE id = 1", severity=Severity.HIGH)
        result = rewrite_query(scored)
        assert not result.has_suggestions

    def test_query_preserved_on_result(self):
        q = "SELECT id FROM t WHERE id NOT IN (1,2)"
        scored = _make_scored(q, severity=Severity.HIGH)
        result = rewrite_query(scored)
        assert result.query == q


# ---------------------------------------------------------------------------
# rewrite_queries
# ---------------------------------------------------------------------------

def test_rewrite_queries_returns_list():
    items = [_make_scored("SELECT * FROM t"), _make_scored("SELECT id FROM t")]
    results = rewrite_queries(items)
    assert len(results) == 2
    assert all(isinstance(r, RewriteResult) for r in results)


# ---------------------------------------------------------------------------
# Formatter
# ---------------------------------------------------------------------------

class TestTruncate:
    def test_short_string_unchanged(self):
        assert _truncate("hello") == "hello"

    def test_long_string_truncated(self):
        s = "x" * 200
        result = _truncate(s)
        assert result.endswith("...")
        assert len(result) == 120


class TestFormatRewriteReport:
    def test_empty_list_returns_message(self):
        out = format_rewrite_report([])
        assert "No rewrite results" in out

    def test_header_present(self):
        scored = _make_scored("SELECT * FROM t")
        results = rewrite_queries([scored])
        out = format_rewrite_report(results)
        assert "Query Rewrite Report" in out

    def test_actionable_count_shown(self):
        items = [_make_scored("SELECT * FROM t"), _make_scored("SELECT id FROM t")]
        results = rewrite_queries(items)
        out = format_rewrite_report(results)
        assert "Queries with rewrites" in out

    def test_no_actionable_shows_fallback(self):
        scored = _make_scored("SELECT id FROM users WHERE id = 1", severity=Severity.HIGH)
        results = rewrite_queries([scored])
        out = format_rewrite_report(results)
        assert "no rewrites suggested" in out.lower() or "All queries look fine" in out
