"""Tests for sqlsift.cache_formatter."""
from __future__ import annotations

from sqlsift.cache_formatter import (
    _truncate,
    format_cache_entry,
    format_cache_report,
)
from sqlsift.query_cache import CacheEntry, CacheReport


class TestTruncate:
    def test_short_string_unchanged(self):
        assert _truncate("SELECT 1") == "SELECT 1"

    def test_long_string_truncated(self):
        long = "A" * 80
        result = _truncate(long)
        assert len(result) == 60
        assert result.endswith("...")

    def test_exactly_max_len_unchanged(self):
        s = "B" * 60
        assert _truncate(s) == s


class TestFormatCacheEntry:
    def test_contains_hit_count(self):
        e = CacheEntry(query="SELECT 1", hit_count=3, miss_count=1)
        out = format_cache_entry(e)
        assert "hits=3" in out

    def test_contains_miss_count(self):
        e = CacheEntry(query="SELECT 1", hit_count=1, miss_count=4)
        out = format_cache_entry(e)
        assert "misses=4" in out

    def test_ratio_formatted_as_percentage(self):
        e = CacheEntry(query="SELECT 1", hit_count=1, miss_count=1)
        out = format_cache_entry(e)
        assert "50.0%" in out

    def test_long_query_truncated_in_output(self):
        e = CacheEntry(query="Q" * 80, hit_count=0, miss_count=1)
        out = format_cache_entry(e)
        assert "..." in out

    def test_zero_calls_ratio_zero(self):
        e = CacheEntry(query="SELECT 1", hit_count=0, miss_count=0)
        out = format_cache_entry(e)
        assert "0.0%" in out


class TestFormatCacheReport:
    def _make_report(self, entries: dict | None = None) -> CacheReport:
        r = CacheReport()
        if entries:
            r.entries = entries
        return r

    def test_header_present(self):
        report = self._make_report()
        out = format_cache_report(report)
        assert "Query Cache Report" in out

    def test_empty_report_shows_no_queries(self):
        report = self._make_report()
        out = format_cache_report(report)
        assert "No queries recorded" in out

    def test_total_calls_shown(self):
        e = CacheEntry(query="SELECT 1", hit_count=2, miss_count=3)
        report = self._make_report({"SELECT 1": e})
        out = format_cache_report(report)
        assert "5" in out

    def test_overall_hit_ratio_shown(self):
        e = CacheEntry(query="SELECT 1", hit_count=1, miss_count=1)
        report = self._make_report({"SELECT 1": e})
        out = format_cache_report(report)
        assert "50.0%" in out

    def test_entries_listed(self):
        e = CacheEntry(query="SELECT 42", hit_count=1, miss_count=0)
        report = self._make_report({"SELECT 42": e})
        out = format_cache_report(report)
        assert "SELECT 42" in out

    def test_sorted_by_hit_ratio_descending(self):
        e1 = CacheEntry(query="FAST", hit_count=9, miss_count=1)
        e2 = CacheEntry(query="SLOW", hit_count=1, miss_count=9)
        report = self._make_report({"FAST": e1, "SLOW": e2})
        out = format_cache_report(report)
        assert out.index("FAST") < out.index("SLOW")
