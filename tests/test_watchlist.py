"""Tests for sqlsift.watchlist."""

from __future__ import annotations

from typing import List

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.watchlist import (
    WatchlistEntry,
    WatchedResult,
    apply_watchlist,
    build_watchlist,
    format_watchlist_report,
)


def _make_result(query: str, duration: float = 100.0) -> AnalysisResult:
    entry = QueryEntry(timestamp="2024-01-01T00:00:00", duration=duration, query=query)
    return AnalysisResult(entry=entry, is_slow=duration >= 100.0, suggestions=[])


# ---------------------------------------------------------------------------
# WatchlistEntry
# ---------------------------------------------------------------------------

class TestWatchlistEntry:
    def test_matches_case_insensitive(self):
        entry = WatchlistEntry(pattern="SELECT \\*", label="star-select")
        assert entry.matches("select * from users")

    def test_no_match_returns_false(self):
        entry = WatchlistEntry(pattern="DROP TABLE", label="dangerous")
        assert not entry.matches("SELECT id FROM users")

    def test_label_defaults_to_empty_string(self):
        entry = WatchlistEntry(pattern="LIKE '%")
        assert entry.label == ""


# ---------------------------------------------------------------------------
# build_watchlist
# ---------------------------------------------------------------------------

class TestBuildWatchlist:
    def test_empty_list_returns_empty(self):
        assert build_watchlist([]) == []

    def test_missing_pattern_skipped(self):
        result = build_watchlist([{"label": "oops"}])
        assert result == []

    def test_label_taken_from_dict(self):
        entries = build_watchlist([{"pattern": "LIKE", "label": "like-query"}])
        assert len(entries) == 1
        assert entries[0].label == "like-query"

    def test_label_defaults_to_pattern_when_absent(self):
        entries = build_watchlist([{"pattern": "LIKE"}])
        assert entries[0].label == "LIKE"

    def test_multiple_patterns_all_built(self):
        entries = build_watchlist([
            {"pattern": "SELECT \\*", "label": "star"},
            {"pattern": "JOIN", "label": "join"},
        ])
        assert len(entries) == 2


# ---------------------------------------------------------------------------
# apply_watchlist
# ---------------------------------------------------------------------------

class TestApplyWatchlist:
    def test_empty_results_returns_empty(self):
        wl = build_watchlist([{"pattern": "SELECT", "label": "sel"}])
        assert apply_watchlist([], wl) == []

    def test_empty_watchlist_returns_empty(self):
        results = [_make_result("SELECT * FROM t")]
        assert apply_watchlist(results, []) == []

    def test_matching_result_included(self):
        results = [_make_result("SELECT * FROM users")]
        wl = build_watchlist([{"pattern": "SELECT \\*", "label": "star"}])
        watched = apply_watchlist(results, wl)
        assert len(watched) == 1
        assert watched[0].matched_labels == ["star"]

    def test_non_matching_result_excluded(self):
        results = [_make_result("INSERT INTO t VALUES (1)")]
        wl = build_watchlist([{"pattern": "SELECT \\*", "label": "star"}])
        assert apply_watchlist(results, wl) == []

    def test_multiple_labels_when_multiple_patterns_match(self):
        results = [_make_result("SELECT * FROM users JOIN orders ON ...")]
        wl = build_watchlist([
            {"pattern": "SELECT \\*", "label": "star"},
            {"pattern": "JOIN", "label": "join"},
        ])
        watched = apply_watchlist(results, wl)
        assert len(watched) == 1
        assert set(watched[0].matched_labels) == {"star", "join"}

    def test_returns_watched_result_instances(self):
        results = [_make_result("SELECT 1")]
        wl = build_watchlist([{"pattern": "SELECT", "label": "sel"}])
        watched = apply_watchlist(results, wl)
        assert isinstance(watched[0], WatchedResult)


# ---------------------------------------------------------------------------
# format_watchlist_report
# ---------------------------------------------------------------------------

class TestFormatWatchlistReport:
    def test_empty_input_returns_no_matches_message(self):
        assert format_watchlist_report([]) == "No watchlist matches found."

    def test_report_contains_hit_count(self):
        results = [_make_result("SELECT * FROM t", duration=200.0)]
        wl = build_watchlist([{"pattern": "SELECT", "label": "sel"}])
        watched = apply_watchlist(results, wl)
        report = format_watchlist_report(watched)
        assert "Watchlist hits: 1" in report

    def test_report_contains_label(self):
        results = [_make_result("SELECT * FROM t", duration=200.0)]
        wl = build_watchlist([{"pattern": "SELECT", "label": "my-label"}])
        watched = apply_watchlist(results, wl)
        report = format_watchlist_report(watched)
        assert "my-label" in report

    def test_report_contains_duration(self):
        results = [_make_result("SELECT 1", duration=150.0)]
        wl = build_watchlist([{"pattern": "SELECT", "label": "s"}])
        watched = apply_watchlist(results, wl)
        report = format_watchlist_report(watched)
        assert "150.0ms" in report
