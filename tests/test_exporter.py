"""Tests for sqlsift.exporter — JSON and CSV export functionality."""

from __future__ import annotations

import csv
import io
import json
import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.exporter import export_csv, export_json, export_results


def _make_result(
    query: str = "SELECT 1",
    duration_ms: float = 100.0,
    is_slow: bool = False,
    suggestions: list[str] | None = None,
    timestamp: str = "2024-01-01T00:00:00",
) -> AnalysisResult:
    entry = QueryEntry(query=query, duration_ms=duration_ms, timestamp=timestamp)
    return AnalysisResult(entry=entry, is_slow=is_slow, suggestions=suggestions or [])


class TestExportJson:
    def test_empty_list_returns_empty_array(self):
        output = export_json([])
        assert json.loads(output) == []

    def test_single_result_structure(self):
        result = _make_result(query="SELECT * FROM users", duration_ms=250.0, is_slow=True)
        data = json.loads(export_json([result]))
        assert len(data) == 1
        row = data[0]
        assert row["query"] == "SELECT * FROM users"
        assert row["duration_ms"] == 250.0
        assert row["is_slow"] is True
        assert row["suggestions"] == []

    def test_suggestions_preserved(self):
        result = _make_result(suggestions=["Add an index", "Avoid SELECT *"])
        data = json.loads(export_json([result]))
        assert data[0]["suggestions"] == ["Add an index", "Avoid SELECT *"]

    def test_multiple_results(self):
        results = [_make_result(duration_ms=float(i)) for i in range(5)]
        data = json.loads(export_json(results))
        assert len(data) == 5


class TestExportCsv:
    def _parse_csv(self, csv_str: str) -> list[dict]:
        return list(csv.DictReader(io.StringIO(csv_str)))

    def test_empty_list_returns_header_only(self):
        output = export_csv([])
        rows = self._parse_csv(output)
        assert rows == []

    def test_single_result_fields(self):
        result = _make_result(query="SELECT id FROM t", duration_ms=500.0, is_slow=True)
        rows = self._parse_csv(export_csv([result]))
        assert len(rows) == 1
        assert rows[0]["query"] == "SELECT id FROM t"
        assert rows[0]["is_slow"] == "True"
        assert rows[0]["duration_ms"] == "500.0"

    def test_suggestions_joined_with_pipe(self):
        result = _make_result(suggestions=["Tip A", "Tip B"])
        rows = self._parse_csv(export_csv([result]))
        assert rows[0]["suggestions"] == "Tip A | Tip B"

    def test_no_suggestions_empty_string(self):
        result = _make_result(suggestions=[])
        rows = self._parse_csv(export_csv([result]))
        assert rows[0]["suggestions"] == ""


class TestExportResults:
    def test_json_format_dispatches_correctly(self):
        result = _make_result()
        output = export_results([result], fmt="json")
        data = json.loads(output)
        assert isinstance(data, list)

    def test_csv_format_dispatches_correctly(self):
        result = _make_result()
        output = export_results([result], fmt="csv")
        assert "query" in output

    def test_case_insensitive_format(self):
        result = _make_result()
        assert export_results([result], fmt="JSON") == export_results([result], fmt="json")

    def test_unsupported_format_raises(self):
        with pytest.raises(ValueError, match="Unsupported export format"):
            export_results([], fmt="xml")
