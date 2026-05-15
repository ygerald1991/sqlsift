"""Tests for sqlsift.snapshot."""
import json
import os
import tempfile

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.snapshot import (
    Snapshot,
    create_snapshot,
    diff_snapshots,
    load_snapshot,
    save_snapshot,
)


def _make_result(query: str, duration: float, is_slow: bool, suggestions=None):
    from sqlsift.parser import QueryEntry
    entry = QueryEntry(timestamp="2024-01-01T00:00:00", duration=duration, query=query)
    return AnalysisResult(
        entry=entry,
        is_slow=is_slow,
        suggestions=suggestions or [],
    )


class TestCreateSnapshot:
    def test_empty_results_produces_snapshot(self):
        snap = create_snapshot([], label="empty")
        assert snap.query_count == 0
        assert snap.slow_count == 0
        assert snap.label == "empty"

    def test_timestamp_injected_when_not_provided(self):
        snap = create_snapshot([])
        assert snap.timestamp  # non-empty string

    def test_explicit_timestamp_preserved(self):
        snap = create_snapshot([], timestamp="2024-06-01T12:00:00+00:00")
        assert snap.timestamp == "2024-06-01T12:00:00+00:00"

    def test_slow_count_reflects_results(self):
        results = [
            _make_result("SELECT 1", 0.5, False),
            _make_result("SELECT 2", 5.0, True),
            _make_result("SELECT 3", 6.0, True),
        ]
        snap = create_snapshot(results)
        assert snap.query_count == 3
        assert snap.slow_count == 2

    def test_results_serialized_as_dicts(self):
        results = [_make_result("SELECT 1", 1.0, False)]
        snap = create_snapshot(results)
        assert isinstance(snap.results[0], dict)
        assert "query" in snap.results[0]


class TestSaveLoadSnapshot:
    def test_round_trip_preserves_fields(self):
        results = [_make_result("SELECT id FROM t", 2.5, True, ["Add index"])]
        snap = create_snapshot(results, label="v1", timestamp="2024-01-01T00:00:00+00:00")
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_snapshot(snap, path)
            loaded = load_snapshot(path)
            assert loaded.label == "v1"
            assert loaded.timestamp == "2024-01-01T00:00:00+00:00"
            assert loaded.query_count == 1
        finally:
            os.unlink(path)

    def test_saved_file_is_valid_json(self):
        snap = create_snapshot([], label="test")
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_snapshot(snap, path)
            with open(path) as fh:
                data = json.load(fh)
            assert data["label"] == "test"
        finally:
            os.unlink(path)


class TestDiffSnapshots:
    def _snap(self, entries):
        """entries: list of (query, is_slow)"""
        results = [_make_result(q, 1.0, s) for q, s in entries]
        return create_snapshot(results)

    def test_empty_snapshots_produce_empty_diff(self):
        diff = diff_snapshots(self._snap([]), self._snap([]))
        assert diff["added_queries"] == []
        assert diff["removed_queries"] == []
        assert diff["newly_slow_queries"] == []

    def test_added_query_detected(self):
        before = self._snap([("SELECT 1", False)])
        after = self._snap([("SELECT 1", False), ("SELECT 2", False)])
        diff = diff_snapshots(before, after)
        assert "SELECT 2" in diff["added_queries"]

    def test_removed_query_detected(self):
        before = self._snap([("SELECT 1", False), ("SELECT 2", False)])
        after = self._snap([("SELECT 1", False)])
        diff = diff_snapshots(before, after)
        assert "SELECT 2" in diff["removed_queries"]

    def test_newly_slow_query_detected(self):
        before = self._snap([("SELECT heavy", False)])
        after = self._snap([("SELECT heavy", True)])
        diff = diff_snapshots(before, after)
        assert "SELECT heavy" in diff["newly_slow_queries"]

    def test_slow_counts_reported(self):
        before = self._snap([("SELECT a", True)])
        after = self._snap([("SELECT a", True), ("SELECT b", True)])
        diff = diff_snapshots(before, after)
        assert diff["slow_count_before"] == 1
        assert diff["slow_count_after"] == 2
