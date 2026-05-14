"""Tests for sqlsift.deduplicator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.deduplicator import (
    DeduplicatedGroup,
    deduplicate,
    top_duplicate_patterns,
)


def _make_result(
    query: str,
    duration: float = 1.0,
    suggestions: List[str] | None = None,
) -> AnalysisResult:
    entry = QueryEntry(timestamp="2024-01-01T00:00:00", duration=duration, query=query)
    return AnalysisResult(
        entry=entry,
        is_slow=duration >= 1.0,
        suggestions=suggestions or [],
    )


class TestDeduplicate:
    def test_empty_input_returns_empty_dict(self):
        assert deduplicate([]) == {}

    def test_single_result_creates_one_group(self):
        result = _make_result("SELECT * FROM users WHERE id = 1")
        groups = deduplicate([result])
        assert len(groups) == 1

    def test_identical_queries_grouped_together(self):
        r1 = _make_result("SELECT * FROM users WHERE id = 1")
        r2 = _make_result("SELECT * FROM users WHERE id = 2")
        groups = deduplicate([r1, r2])
        # Both normalize to same pattern — only one group
        assert len(groups) == 1
        group = next(iter(groups.values()))
        assert group.count == 2

    def test_different_queries_create_separate_groups(self):
        r1 = _make_result("SELECT * FROM users WHERE id = 1")
        r2 = _make_result("SELECT * FROM orders WHERE id = 1")
        groups = deduplicate([r1, r2])
        assert len(groups) == 2

    def test_group_avg_duration(self):
        r1 = _make_result("SELECT * FROM users WHERE id = 1", duration=2.0)
        r2 = _make_result("SELECT * FROM users WHERE id = 2", duration=4.0)
        groups = deduplicate([r1, r2])
        group = next(iter(groups.values()))
        assert group.avg_duration == pytest.approx(3.0)

    def test_group_max_duration(self):
        r1 = _make_result("SELECT * FROM users WHERE id = 1", duration=1.0)
        r2 = _make_result("SELECT * FROM users WHERE id = 2", duration=5.0)
        groups = deduplicate([r1, r2])
        group = next(iter(groups.values()))
        assert group.max_duration == pytest.approx(5.0)

    def test_all_suggestions_are_unique(self):
        r1 = _make_result("SELECT * FROM t WHERE x = 1", suggestions=["Add index", "Avoid SELECT *"])
        r2 = _make_result("SELECT * FROM t WHERE x = 2", suggestions=["Add index", "Use LIMIT"])
        groups = deduplicate([r1, r2])
        group = next(iter(groups.values()))
        assert group.all_suggestions == ["Add index", "Avoid SELECT *", "Use LIMIT"]


class TestTopDuplicatePatterns:
    def test_empty_input_returns_empty_list(self):
        assert top_duplicate_patterns([]) == []

    def test_returns_at_most_limit_groups(self):
        results = [
            _make_result(f"SELECT * FROM table_{i} WHERE id = 1")
            for i in range(10)
        ]
        top = top_duplicate_patterns(results, limit=3)
        assert len(top) <= 3

    def test_most_frequent_pattern_is_first(self):
        common = [_make_result("SELECT * FROM users WHERE id = 1") for _ in range(5)]
        rare = [_make_result("SELECT * FROM orders WHERE id = 1")]
        top = top_duplicate_patterns(common + rare, limit=5)
        assert top[0].count == 5

    def test_default_limit_is_five(self):
        results = [
            _make_result(f"SELECT col FROM tbl_{i} WHERE val = 1")
            for i in range(10)
        ]
        top = top_duplicate_patterns(results)
        assert len(top) <= 5
