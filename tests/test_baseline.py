"""Tests for sqlsift.baseline."""

import json
import tempfile
from pathlib import Path

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.baseline import (
    Baseline,
    BaselineEntry,
    build_baseline,
    load_baseline,
    save_baseline,
)
from sqlsift.parser import QueryEntry


def _make_result(query: str, duration: float, suggestions=None, is_slow=True):
    entry = QueryEntry(timestamp="2024-01-01T00:00:00", duration=duration, query=query)
    return AnalysisResult(
        entry=entry,
        is_slow=is_slow,
        suggestions=suggestions or [],
    )


class TestBuildBaseline:
    def test_empty_input_returns_empty_baseline(self):
        baseline = build_baseline([])
        assert baseline.entries == {}

    def test_single_result_creates_entry(self):
        r = _make_result("SELECT 1", 1.5, ["use index"])
        baseline = build_baseline([r])
        assert "SELECT 1" in baseline.entries
        e = baseline.entries["SELECT 1"]
        assert e.avg_duration == 1.5
        assert e.suggestion_count == 1
        assert e.occurrences == 1

    def test_duplicate_queries_averaged(self):
        r1 = _make_result("SELECT 1", 1.0)
        r2 = _make_result("SELECT 1", 3.0)
        baseline = build_baseline([r1, r2])
        e = baseline.entries["SELECT 1"]
        assert e.avg_duration == pytest.approx(2.0)
        assert e.occurrences == 2

    def test_suggestion_count_takes_maximum(self):
        r1 = _make_result("SELECT 1", 1.0, ["a"])
        r2 = _make_result("SELECT 1", 2.0, ["a", "b", "c"])
        baseline = build_baseline([r1, r2])
        assert baseline.entries["SELECT 1"].suggestion_count == 3

    def test_multiple_distinct_queries(self):
        r1 = _make_result("SELECT 1", 1.0)
        r2 = _make_result("SELECT 2", 2.0)
        baseline = build_baseline([r1, r2])
        assert len(baseline.entries) == 2

    def test_get_returns_none_for_missing_query(self):
        baseline = build_baseline([])
        assert baseline.get("MISSING") is None

    def test_get_returns_entry_for_known_query(self):
        r = _make_result("SELECT 1", 1.0)
        baseline = build_baseline([r])
        assert baseline.get("SELECT 1") is not None


class TestSaveLoadBaseline:
    def test_roundtrip_preserves_data(self):
        r = _make_result("SELECT 1", 2.5, ["use index"])
        baseline = build_baseline([r])
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        save_baseline(baseline, path)
        loaded = load_baseline(path)
        assert "SELECT 1" in loaded.entries
        e = loaded.entries["SELECT 1"]
        assert e.avg_duration == pytest.approx(2.5)
        assert e.suggestion_count == 1
        assert e.occurrences == 1

    def test_saved_file_is_valid_json(self):
        r = _make_result("SELECT 1", 1.0)
        baseline = build_baseline([r])
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        save_baseline(baseline, path)
        data = json.loads(Path(path).read_text())
        assert isinstance(data, list)
        assert data[0]["query"] == "SELECT 1"

    def test_empty_baseline_saves_empty_array(self):
        baseline = build_baseline([])
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        save_baseline(baseline, path)
        data = json.loads(Path(path).read_text())
        assert data == []
