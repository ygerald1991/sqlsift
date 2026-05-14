"""Tests for sqlsift.labeler."""

from __future__ import annotations

from typing import List

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.labeler import LabeledResult, label_result, label_results


def _make_result(query: str, duration: float = 0.1, suggestions: List[str] | None = None) -> AnalysisResult:
    entry = QueryEntry(timestamp="2024-01-01T00:00:00", duration=duration, query=query)
    return AnalysisResult(entry=entry, is_slow=duration >= 1.0, suggestions=suggestions or [])


class TestLabelResult:
    def test_returns_labeled_result_instance(self):
        result = _make_result("SELECT 1")
        labeled = label_result(result)
        assert isinstance(labeled, LabeledResult)

    def test_result_attribute_preserved(self):
        result = _make_result("SELECT id FROM users")
        labeled = label_result(result)
        assert labeled.result is result

    def test_simple_select_label(self):
        labeled = label_result(_make_result("SELECT id FROM users WHERE id = 1"))
        assert labeled.label == "simple-read"

    def test_join_query_label(self):
        labeled = label_result(_make_result("SELECT u.id FROM users u JOIN orders o ON u.id = o.user_id"))
        assert labeled.label == "join-query"

    def test_aggregation_label(self):
        labeled = label_result(_make_result("SELECT count(*) FROM orders GROUP BY user_id"))
        assert labeled.label == "aggregation"

    def test_sorted_read_label(self):
        labeled = label_result(_make_result("SELECT name FROM users ORDER BY name ASC"))
        assert labeled.label == "sorted-read"

    def test_pattern_match_label(self):
        labeled = label_result(_make_result("SELECT name FROM users WHERE name LIKE '%john%'"))
        assert labeled.label == "pattern-match"

    def test_in_clause_label(self):
        labeled = label_result(_make_result("SELECT id FROM users WHERE id IN (1, 2, 3)"))
        assert labeled.label == "in-clause"

    def test_insert_label(self):
        labeled = label_result(_make_result("INSERT INTO users (name) VALUES ('alice')"))
        assert labeled.label == "write-insert"

    def test_update_label(self):
        labeled = label_result(_make_result("UPDATE users SET name = 'bob' WHERE id = 1"))
        assert labeled.label == "write-update"

    def test_delete_label(self):
        labeled = label_result(_make_result("DELETE FROM users WHERE id = 1"))
        assert labeled.label == "write-delete"

    def test_ddl_create_label(self):
        labeled = label_result(_make_result("CREATE TABLE foo (id INT)"))
        assert labeled.label == "ddl"

    def test_unknown_label_for_unrecognised_query(self):
        labeled = label_result(_make_result("EXPLAIN SELECT 1"))
        assert labeled.label == "unknown"

    def test_limited_extra_label(self):
        labeled = label_result(_make_result("SELECT id FROM users LIMIT 10"))
        assert "limited" in labeled.extra_labels

    def test_distinct_extra_label(self):
        labeled = label_result(_make_result("SELECT DISTINCT name FROM users"))
        assert "distinct" in labeled.extra_labels

    def test_all_labels_combines_primary_and_extra(self):
        labeled = label_result(_make_result("SELECT DISTINCT id FROM users LIMIT 5"))
        assert labeled.label in labeled.all_labels
        assert "distinct" in labeled.all_labels
        assert "limited" in labeled.all_labels

    def test_no_extra_labels_by_default(self):
        labeled = label_result(_make_result("SELECT id FROM users"))
        assert labeled.extra_labels == []


class TestLabelResults:
    def test_empty_input_returns_empty_list(self):
        assert label_results([]) == []

    def test_length_preserved(self):
        results = [_make_result("SELECT 1"), _make_result("INSERT INTO t VALUES (1)")]
        labeled = label_results(results)
        assert len(labeled) == 2

    def test_each_element_is_labeled_result(self):
        results = [_make_result("SELECT 1"), _make_result("DELETE FROM t WHERE id=1")]
        for lr in label_results(results):
            assert isinstance(lr, LabeledResult)
