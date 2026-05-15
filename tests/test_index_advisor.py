"""Tests for sqlsift.index_advisor."""
import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.scorer import ScoredResult, Severity
from sqlsift.index_advisor import (
    IndexSuggestion,
    IndexAdvice,
    advise_indexes,
    advise_all,
)


def _make_scored(query: str, severity: Severity, duration: float = 2000.0) -> ScoredResult:
    entry = QueryEntry(
        timestamp="2024-01-01T00:00:00",
        duration_ms=duration,
        query=query,
        user="test",
        database="db",
    )
    result = AnalysisResult(
        entry=entry,
        is_slow=severity in (Severity.HIGH, Severity.CRITICAL),
        suggestions=[],
    )
    return ScoredResult(result=result, score=80.0, severity=severity)


class TestAdviseIndexes:
    def test_low_severity_returns_no_suggestions(self):
        sr = _make_scored("SELECT * FROM orders WHERE id = 1", Severity.LOW)
        advice = advise_indexes(sr)
        assert not advice.has_suggestions
        assert advice.suggestions == []

    def test_medium_severity_returns_no_suggestions(self):
        sr = _make_scored("SELECT * FROM orders WHERE id = 1", Severity.MEDIUM)
        advice = advise_indexes(sr)
        assert not advice.has_suggestions

    def test_high_severity_where_column_detected(self):
        sr = _make_scored(
            "SELECT * FROM users WHERE email = 'a@b.com'", Severity.HIGH
        )
        advice = advise_indexes(sr)
        assert advice.has_suggestions
        assert any("email" in s.columns for s in advice.suggestions)

    def test_critical_severity_where_column_detected(self):
        sr = _make_scored(
            "SELECT id FROM orders WHERE status = 'open'", Severity.CRITICAL
        )
        advice = advise_indexes(sr)
        assert advice.has_suggestions
        assert any("status" in s.columns for s in advice.suggestions)

    def test_order_by_column_detected(self):
        sr = _make_scored(
            "SELECT * FROM products WHERE price > 10 ORDER BY created_at",
            Severity.HIGH,
        )
        advice = advise_indexes(sr)
        cols = [c for s in advice.suggestions for c in s.columns]
        assert "created_at" in cols

    def test_table_inferred_from_from_clause(self):
        sr = _make_scored(
            "SELECT * FROM invoices WHERE amount > 100", Severity.HIGH
        )
        advice = advise_indexes(sr)
        tables = [s.table for s in advice.suggestions]
        assert any(t == "invoices" for t in tables)

    def test_query_preserved_on_advice(self):
        query = "SELECT * FROM logs WHERE level = 'error'"
        sr = _make_scored(query, Severity.CRITICAL)
        advice = advise_indexes(sr)
        assert advice.query == query

    def test_index_suggestion_str(self):
        s = IndexSuggestion(table="users", columns=["email"], reason="used in WHERE")
        text = str(s)
        assert "CREATE INDEX" in text
        assert "users" in text
        assert "email" in text


class TestAdviseAll:
    def test_empty_input_returns_empty_dict(self):
        assert advise_all([]) == {}

    def test_only_high_severity_included(self):
        low = _make_scored("SELECT 1", Severity.LOW)
        high = _make_scored(
            "SELECT * FROM orders WHERE id = 5", Severity.HIGH
        )
        result = advise_all([low, high])
        assert len(result) == 1
        assert "orders" in next(iter(result.values())).suggestions[0].table

    def test_multiple_high_severity_all_included(self):
        s1 = _make_scored("SELECT * FROM a WHERE x = 1", Severity.HIGH)
        s2 = _make_scored("SELECT * FROM b WHERE y = 2", Severity.CRITICAL)
        result = advise_all([s1, s2])
        assert len(result) == 2
