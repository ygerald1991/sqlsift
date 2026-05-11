"""Tests for the sqlsift query log parser."""

import pytest
from sqlsift.parser import QueryEntry, parse_line, parse_log


SAMPLE_LINE = (
    "# Time: 2024-01-15T10:23:45 | User: admin | DB: mydb "
    "| Duration: 1234.5ms | Query: SELECT * FROM orders WHERE status = 'pending'"
)

MINIMAL_LINE = "Duration: 50ms | Query: SELECT 1"

INVALID_LINE = "This is not a valid log line"


class TestParseLine:
    def test_full_entry_parsed_correctly(self):
        entry = parse_line(SAMPLE_LINE)
        assert entry is not None
        assert entry.raw_query == "SELECT * FROM orders WHERE status = 'pending'"
        assert entry.duration_ms == 1234.5
        assert entry.timestamp == "2024-01-15T10:23:45"
        assert entry.user == "admin"
        assert entry.database == "mydb"

    def test_minimal_entry_parsed_correctly(self):
        entry = parse_line(MINIMAL_LINE)
        assert entry is not None
        assert entry.raw_query == "SELECT 1"
        assert entry.duration_ms == 50.0
        assert entry.timestamp is None
        assert entry.user is None
        assert entry.database is None

    def test_invalid_line_returns_none(self):
        assert parse_line(INVALID_LINE) is None

    def test_empty_line_returns_none(self):
        assert parse_line("") is None
        assert parse_line("   ") is None


class TestQueryEntry:
    def test_is_slow_above_threshold(self):
        entry = QueryEntry(raw_query="SELECT 1", duration_ms=1500.0)
        assert entry.is_slow(threshold_ms=1000.0) is True

    def test_is_slow_below_threshold(self):
        entry = QueryEntry(raw_query="SELECT 1", duration_ms=200.0)
        assert entry.is_slow(threshold_ms=1000.0) is False

    def test_is_slow_at_threshold(self):
        entry = QueryEntry(raw_query="SELECT 1", duration_ms=1000.0)
        assert entry.is_slow(threshold_ms=1000.0) is True

    def test_default_tags_are_empty(self):
        entry = QueryEntry(raw_query="SELECT 1", duration_ms=10.0)
        assert entry.tags == []


class TestParseLog:
    def test_parse_multiple_lines(self):
        log_text = "\n".join([SAMPLE_LINE, MINIMAL_LINE, INVALID_LINE, ""])
        entries = parse_log(log_text)
        assert len(entries) == 2
        assert entries[0].duration_ms == 1234.5
        assert entries[1].duration_ms == 50.0

    def test_empty_log_returns_empty_list(self):
        assert parse_log("") == []

    def test_all_invalid_lines_returns_empty_list(self):
        assert parse_log("bad line\nanother bad line") == []
