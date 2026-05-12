"""Tests for sqlsift.analyzer module."""

import pytest
from sqlsift.parser import QueryEntry
from sqlsift.analyzer import (
    analyze_entry,
    analyze_entries,
    AnalysisResult,
    DEFAULT_SLOW_THRESHOLD_MS,
)


def _make_entry(query: str, duration_ms: float = 500.0) -> QueryEntry:
    return QueryEntry(
        timestamp="2024-01-15T10:00:00",
        duration_ms=duration_ms,
        query=query,
        user=None,
        host=None,
    )


class TestAnalyzeEntry:
    def test_fast_query_not_slow(self):
        entry = _make_entry("SELECT id FROM users WHERE id = 1", duration_ms=200.0)
        result = analyze_entry(entry)
        assert result.is_slow is False
        assert result.duration_ms == 200.0

    def test_slow_query_detected(self):
        entry = _make_entry("SELECT id FROM users", duration_ms=1500.0)
        result = analyze_entry(entry)
        assert result.is_slow is True

    def test_query_at_threshold_is_slow(self):
        entry = _make_entry("SELECT 1", duration_ms=DEFAULT_SLOW_THRESHOLD_MS)
        result = analyze_entry(entry)
        assert result.is_slow is True

    def test_custom_threshold(self):
        entry = _make_entry("SELECT 1", duration_ms=300.0)
        result = analyze_entry(entry, slow_threshold_ms=500.0)
        assert result.is_slow is False
        result2 = analyze_entry(entry, slow_threshold_ms=200.0)
        assert result2.is_slow is True

    def test_select_star_suggestion(self):
        entry = _make_entry("SELECT * FROM orders")
        result = analyze_entry(entry)
        assert any("SELECT *" in s for s in result.suggestions)

    def test_leading_wildcard_suggestion(self):
        entry = _make_entry("SELECT id FROM users WHERE name LIKE '%smith'")
        result = analyze_entry(entry)
        assert any("wildcard" in s.lower() for s in result.suggestions)

    def test_no_suggestions_for_clean_query(self):
        entry = _make_entry("SELECT id, name FROM users WHERE id = 42")
        result = analyze_entry(entry)
        assert result.suggestions == []
        assert result.has_suggestions() is False

    def test_none_duration_treated_as_zero(self):
        entry = QueryEntry(
            timestamp="2024-01-15T10:00:00",
            duration_ms=None,
            query="SELECT 1",
            user=None,
            host=None,
        )
        result = analyze_entry(entry)
        assert result.duration_ms == 0.0
        assert result.is_slow is False


class TestAnalyzeEntries:
    def test_returns_all_results_by_default(self):
        entries = [
            _make_entry("SELECT 1", 100.0),
            _make_entry("SELECT * FROM t", 2000.0),
        ]
        results = analyze_entries(entries)
        assert len(results) == 2

    def test_only_slow_filters_correctly(self):
        entries = [
            _make_entry("SELECT 1", 100.0),
            _make_entry("SELECT * FROM t", 2000.0),
            _make_entry("SELECT id FROM t", 1200.0),
        ]
        results = analyze_entries(entries, only_slow=True)
        assert len(results) == 2
        assert all(r.is_slow for r in results)

    def test_empty_list_returns_empty(self):
        assert analyze_entries([]) == []
