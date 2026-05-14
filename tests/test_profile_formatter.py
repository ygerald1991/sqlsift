"""Tests for sqlsift.profile_formatter."""

from __future__ import annotations

import pytest

from sqlsift.profiler import ProfileEntry
from sqlsift.profile_formatter import (
    _truncate,
    format_profile_entry,
    format_profile_report,
)


def _make_entry(
    pattern: str = "SELECT ? FROM users",
    executions: int = 4,
    total_duration: float = 8.0,
    min_duration: float = 1.0,
    max_duration: float = 3.0,
    slow_count: int = 2,
    suggestions: list[str] | None = None,
) -> ProfileEntry:
    entry = ProfileEntry(
        pattern=pattern,
        executions=executions,
        total_duration=total_duration,
        min_duration=min_duration,
        max_duration=max_duration,
        slow_count=slow_count,
    )
    entry.all_suggestions = suggestions or []
    return entry


class TestTruncate:
    def test_short_string_unchanged(self):
        assert _truncate("short") == "short"

    def test_long_string_truncated(self):
        long = "x" * 100
        result = _truncate(long)
        assert result.endswith("...")
        assert len(result) == 72

    def test_exactly_max_len_unchanged(self):
        s = "a" * 72
        assert _truncate(s) == s


class TestFormatProfileEntry:
    def test_contains_pattern(self):
        entry = _make_entry(pattern="SELECT ? FROM t")
        output = format_profile_entry(entry)
        assert "SELECT ? FROM t" in output

    def test_contains_execution_count(self):
        entry = _make_entry(executions=7)
        output = format_profile_entry(entry)
        assert "7" in output

    def test_contains_avg_duration(self):
        entry = _make_entry(executions=2, total_duration=6.0)
        output = format_profile_entry(entry)
        assert "3.000s" in output

    def test_contains_min_max(self):
        entry = _make_entry(min_duration=0.5, max_duration=4.2)
        output = format_profile_entry(entry)
        assert "0.500s" in output
        assert "4.200s" in output

    def test_contains_slow_ratio(self):
        entry = _make_entry(executions=4, slow_count=2)
        output = format_profile_entry(entry)
        assert "50.0%" in output

    def test_suggestions_listed(self):
        entry = _make_entry(suggestions=["Add index", "Avoid SELECT *"])
        output = format_profile_entry(entry)
        assert "Add index" in output
        assert "Avoid SELECT *" in output

    def test_no_suggestions_section_absent(self):
        entry = _make_entry(suggestions=[])
        output = format_profile_entry(entry)
        assert "Suggestions" not in output


class TestFormatProfileReport:
    def test_empty_profiles_returns_message(self):
        output = format_profile_report({})
        assert "No query profiles available" in output

    def test_report_contains_header(self):
        profiles = {"a": _make_entry(pattern="a")}
        output = format_profile_report(profiles, top_n=1)
        assert "Top" in output

    def test_report_contains_summary(self):
        profiles = {
            "a": _make_entry(pattern="a", executions=3, total_duration=6.0),
            "b": _make_entry(pattern="b", executions=2, total_duration=4.0),
        }
        output = format_profile_report(profiles)
        assert "2 unique pattern" in output
        assert "5 total execution" in output

    def test_rank_labels_present(self):
        profiles = {
            "a": _make_entry(pattern="a", total_duration=10.0),
            "b": _make_entry(pattern="b", total_duration=5.0),
        }
        output = format_profile_report(profiles, top_n=2)
        assert "#1" in output
        assert "#2" in output

    def test_top_n_limits_entries(self):
        profiles = {
            str(i): _make_entry(pattern=str(i), total_duration=float(i))
            for i in range(10)
        }
        output = format_profile_report(profiles, top_n=3)
        assert "#3" in output
        assert "#4" not in output
