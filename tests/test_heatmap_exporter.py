"""Tests for sqlsift.heatmap_exporter."""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime

from sqlsift.analyzer import AnalysisResult
from sqlsift.heatmap import build_heatmap
from sqlsift.heatmap_exporter import export_heatmap_csv, export_heatmap_json
from sqlsift.parser import QueryEntry


def _make_result(duration: float, is_slow: bool, timestamp=None) -> AnalysisResult:
    entry = QueryEntry(timestamp=timestamp, duration=duration, query="SELECT 1")
    return AnalysisResult(entry=entry, is_slow=is_slow, suggestions=[])


class TestExportHeatmapJson:
    def test_returns_string(self):
        hm = build_heatmap([])
        out = export_heatmap_json(hm)
        assert isinstance(out, str)

    def test_parses_as_valid_json(self):
        hm = build_heatmap([])
        data = json.loads(export_heatmap_json(hm))
        assert isinstance(data, list)

    def test_contains_168_cells(self):
        hm = build_heatmap([])
        data = json.loads(export_heatmap_json(hm))
        assert len(data) == 7 * 24

    def test_slow_query_reflected_in_json(self):
        ts = datetime(2024, 1, 1, 6, 0)  # Mon 06
        results = [_make_result(400.0, is_slow=True, timestamp=ts)]
        hm = build_heatmap(results)
        data = json.loads(export_heatmap_json(hm))
        cell = next(r for r in data if r["day"] == "Mon" and r["hour"] == 6)
        assert cell["count"] == 1
        assert cell["total_duration_ms"] == 400.0

    def test_required_keys_present(self):
        hm = build_heatmap([])
        data = json.loads(export_heatmap_json(hm))
        required = {"day", "hour", "count", "total_duration_ms", "avg_duration_ms"}
        assert required.issubset(data[0].keys())


class TestExportHeatmapCsv:
    def test_returns_string(self):
        hm = build_heatmap([])
        assert isinstance(export_heatmap_csv(hm), str)

    def test_csv_has_header_row(self):
        hm = build_heatmap([])
        reader = csv.DictReader(io.StringIO(export_heatmap_csv(hm)))
        assert "count" in (reader.fieldnames or [])

    def test_csv_row_count_matches_cells(self):
        hm = build_heatmap([])
        reader = csv.DictReader(io.StringIO(export_heatmap_csv(hm)))
        rows = list(reader)
        assert len(rows) == 7 * 24
