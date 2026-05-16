"""Tests for sqlsift.execution_tracker."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.execution_tracker import (
    ExecutionRecord,
    ExecutionReport,
    track_executions,
)


def _make_result(query: str, duration: float, is_slow: bool = False) -> AnalysisResult:
    entry = QueryEntry(
        timestamp="2024-01-01T00:00:00",
        duration=duration,
        query=query,
    )
    return AnalysisResult(entry=entry, is_slow=is_slow, suggestions=[])


class TestTrackExecutions:
    def test_empty_input_returns_empty_report(self):
        report = track_executions([])
        assert report.total_queries == 0
        assert report.unique_patterns == 0

    def test_single_result_creates_one_record(self):
        result = _make_result("SELECT id FROM users", 100.0)
        report = track_executions([result])
        assert report.unique_patterns == 1
        assert report.total_queries == 1

    def test_identical_queries_merged_into_one_pattern(self):
        results = [
            _make_result("SELECT id FROM users WHERE id = 1", 50.0),
            _make_result("SELECT id FROM users WHERE id = 2", 80.0),
        ]
        report = track_executions(results)
        assert report.unique_patterns == 1
        assert report.total_queries == 2

    def test_avg_duration_computed_correctly(self):
        results = [
            _make_result("SELECT * FROM orders WHERE id = 1", 100.0),
            _make_result("SELECT * FROM orders WHERE id = 2", 200.0),
        ]
        report = track_executions(results)
        record = list(report.records.values())[0]
        assert record.avg_duration == pytest.approx(150.0)

    def test_max_duration_tracked(self):
        results = [
            _make_result("SELECT name FROM products WHERE id = 1", 30.0),
            _make_result("SELECT name FROM products WHERE id = 2", 999.0),
        ]
        report = track_executions(results)
        record = list(report.records.values())[0]
        assert record.max_duration == pytest.approx(999.0)

    def test_min_duration_tracked(self):
        results = [
            _make_result("SELECT name FROM products WHERE id = 1", 30.0),
            _make_result("SELECT name FROM products WHERE id = 2", 999.0),
        ]
        report = track_executions(results)
        record = list(report.records.values())[0]
        assert record.min_duration == pytest.approx(30.0)

    def test_most_frequent_returns_sorted_records(self):
        results = (
            [_make_result("SELECT id FROM users WHERE id = 1", 10.0)] * 5
            + [_make_result("SELECT id FROM orders WHERE id = 1", 20.0)] * 2
        )
        report = track_executions(results)
        top = report.most_frequent(2)
        assert top[0].call_count >= top[1].call_count

    def test_slowest_avg_returns_sorted_records(self):
        results = [
            _make_result("SELECT a FROM t1 WHERE a = 1", 500.0),
            _make_result("SELECT b FROM t2 WHERE b = 1", 10.0),
        ]
        report = track_executions(results)
        slowest = report.slowest_avg(2)
        assert slowest[0].avg_duration >= slowest[1].avg_duration

    def test_different_queries_create_separate_records(self):
        results = [
            _make_result("SELECT id FROM users WHERE id = 1", 10.0),
            _make_result("DELETE FROM logs WHERE id = 1", 50.0),
        ]
        report = track_executions(results)
        assert report.unique_patterns == 2

    def test_call_count_increments_per_occurrence(self):
        results = [_make_result("SELECT 1 FROM dual", 5.0)] * 7
        report = track_executions(results)
        record = list(report.records.values())[0]
        assert record.call_count == 7
