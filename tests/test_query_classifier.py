"""Tests for sqlsift.query_classifier."""
from __future__ import annotations

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.query_classifier import (
    ClassificationReport,
    ClassifiedResult,
    classify_result,
    classify_results,
)


def _make_result(query: str, duration: float = 1.0, slow: bool = True) -> AnalysisResult:
    entry = QueryEntry(timestamp="2024-01-01T00:00:00", duration=duration, query=query)
    return AnalysisResult(entry=entry, is_slow=slow, suggestions=[])


class TestClassifyResult:
    def test_returns_classified_result_instance(self):
        r = _make_result("SELECT 1")
        cr = classify_result(r)
        assert isinstance(cr, ClassifiedResult)

    def test_select_operation_detected(self):
        cr = classify_result(_make_result("SELECT id FROM users"))
        assert cr.operation == "SELECT"

    def test_insert_operation_detected(self):
        cr = classify_result(_make_result("INSERT INTO users (id) VALUES (1)"))
        assert cr.operation == "INSERT"

    def test_update_operation_detected(self):
        cr = classify_result(_make_result("UPDATE users SET name='x' WHERE id=1"))
        assert cr.operation == "UPDATE"

    def test_delete_operation_detected(self):
        cr = classify_result(_make_result("DELETE FROM users WHERE id=1"))
        assert cr.operation == "DELETE"

    def test_unknown_operation_returns_other(self):
        cr = classify_result(_make_result("EXPLAIN SELECT 1"))
        assert cr.operation == "OTHER"

    def test_join_detected(self):
        cr = classify_result(_make_result("SELECT * FROM a JOIN b ON a.id=b.id"))
        assert cr.has_join is True

    def test_no_join_when_absent(self):
        cr = classify_result(_make_result("SELECT id FROM users"))
        assert cr.has_join is False

    def test_subquery_detected(self):
        cr = classify_result(_make_result("SELECT * FROM (SELECT id FROM users) sub"))
        assert cr.has_subquery is True

    def test_no_subquery_when_absent(self):
        cr = classify_result(_make_result("SELECT id FROM users"))
        assert cr.has_subquery is False

    def test_aggregate_detected(self):
        cr = classify_result(_make_result("SELECT COUNT(*) FROM users"))
        assert cr.has_aggregate is True

    def test_no_aggregate_when_absent(self):
        cr = classify_result(_make_result("SELECT id FROM users"))
        assert cr.has_aggregate is False

    def test_table_count_single(self):
        cr = classify_result(_make_result("SELECT id FROM users"))
        assert cr.table_count >= 1

    def test_table_count_with_join(self):
        cr = classify_result(_make_result("SELECT * FROM a JOIN b ON a.id=b.id"))
        assert cr.table_count >= 2


class TestClassifyResults:
    def test_empty_input_returns_empty_report(self):
        report = classify_results([])
        assert isinstance(report, ClassificationReport)
        assert report.total == 0
        assert report.by_operation == {}

    def test_total_matches_input_length(self):
        results = [_make_result("SELECT 1"), _make_result("INSERT INTO t VALUES (1)")]
        report = classify_results(results)
        assert report.total == 2

    def test_by_operation_groups_correctly(self):
        results = [
            _make_result("SELECT id FROM a"),
            _make_result("SELECT name FROM b"),
            _make_result("DELETE FROM c WHERE id=1"),
        ]
        report = classify_results(results)
        assert report.count_for("SELECT") == 2
        assert report.count_for("DELETE") == 1

    def test_count_for_missing_operation_returns_zero(self):
        report = classify_results([_make_result("SELECT 1")])
        assert report.count_for("DROP") == 0
