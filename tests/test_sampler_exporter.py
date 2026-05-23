"""Tests for sqlsift.sampler_exporter."""
from __future__ import annotations

import csv
import io
import json

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.query_sampler import SampleReport
from sqlsift.sampler_exporter import export_sample, export_sample_csv, export_sample_json


def _make_result(
    query: str = "SELECT 1",
    duration_ms: float = 100.0,
    is_slow: bool = False,
    suggestions: list[str] | None = None,
) -> AnalysisResult:
    entry = QueryEntry(
        timestamp="2024-06-01T12:00:00",
        duration_ms=duration_ms,
        query=query,
        user="u",
        database="d",
    )
    return AnalysisResult(entry=entry, is_slow=is_slow, suggestions=suggestions or [])


def _make_report(n: int = 2) -> SampleReport:
    results = [_make_result(query=f"SELECT {i}", is_slow=(i % 2 == 0)) for i in range(n)]
    return SampleReport(results=results, total_seen=n * 2, sample_size=n)


class TestExportSampleJson:
    def test_returns_string(self):
        assert isinstance(export_sample_json(_make_report()), str)

    def test_parses_as_valid_json(self):
        data = json.loads(export_sample_json(_make_report()))
        assert isinstance(data, dict)

    def test_top_level_keys_present(self):
        data = json.loads(export_sample_json(_make_report(3)))
        for key in ("total_seen", "sample_size", "count", "coverage_ratio", "results"):
            assert key in data

    def test_results_length_matches_report(self):
        report = _make_report(4)
        data = json.loads(export_sample_json(report))
        assert len(data["results"]) == 4

    def test_empty_report_produces_empty_results_array(self):
        report = SampleReport(results=[], total_seen=0, sample_size=10)
        data = json.loads(export_sample_json(report))
        assert data["results"] == []

    def test_coverage_ratio_in_output(self):
        report = _make_report(2)  # total_seen=4, count=2 => 0.5
        data = json.loads(export_sample_json(report))
        assert data["coverage_ratio"] == 0.5


class TestExportSampleCsv:
    def test_returns_string(self):
        assert isinstance(export_sample_csv(_make_report()), str)

    def test_header_row_present(self):
        text = export_sample_csv(_make_report(1))
        assert text.startswith("query,")

    def test_row_count_matches_results(self):
        report = _make_report(3)
        reader = csv.DictReader(io.StringIO(export_sample_csv(report)))
        rows = list(reader)
        assert len(rows) == 3

    def test_suggestions_pipe_separated(self):
        r = _make_result(suggestions=["add index", "avoid SELECT *"])
        report = SampleReport(results=[r], total_seen=1, sample_size=1)
        reader = csv.DictReader(io.StringIO(export_sample_csv(report)))
        row = next(reader)
        assert row["suggestions"] == "add index|avoid SELECT *"


class TestExportSampleDispatch:
    def test_default_format_is_json(self):
        result = export_sample(_make_report())
        json.loads(result)  # should not raise

    def test_csv_format_dispatched(self):
        result = export_sample(_make_report(), fmt="csv")
        assert "query" in result.splitlines()[0]
