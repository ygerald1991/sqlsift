"""Tests for sqlsift.sorter module."""

import pytest
from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.sorter import SortKey, sort_results


def _make_result(
    query: str = "SELECT 1",
    duration_ms: float = 100.0,
    timestamp: str = "2024-01-01T00:00:00",
    suggestions: list | None = None,
) -> AnalysisResult:
    entry = QueryEntry(
        timestamp=timestamp,
        duration_ms=duration_ms,
        query=query,
    )
    return AnalysisResult(
        entry=entry,
        is_slow=duration_ms >= 1000,
        suggestions=suggestions or [],
    )


class TestSortResults:
    def test_sort_by_duration_descending(self):
        results = [_make_result(duration_ms=d) for d in [200, 50, 800]]
        out = sort_results(results, key=SortKey.DURATION, descending=True)
        assert [r.entry.duration_ms for r in out] == [800, 200, 50]

    def test_sort_by_duration_ascending(self):
        results = [_make_result(duration_ms=d) for d in [200, 50, 800]]
        out = sort_results(results, key=SortKey.DURATION, descending=False)
        assert [r.entry.duration_ms for r in out] == [50, 200, 800]

    def test_sort_by_suggestion_count(self):
        results = [
            _make_result(suggestions=["a", "b"]),
            _make_result(suggestions=[]),
            _make_result(suggestions=["x"]),
        ]
        out = sort_results(results, key=SortKey.SUGGESTION_COUNT)
        assert [len(r.suggestions) for r in out] == [2, 1, 0]

    def test_sort_by_query_alphabetical(self):
        results = [
            _make_result(query="SELECT z"),
            _make_result(query="SELECT a"),
            _make_result(query="SELECT m"),
        ]
        out = sort_results(results, key=SortKey.QUERY, descending=False)
        assert out[0].entry.query == "SELECT a"
        assert out[-1].entry.query == "SELECT z"

    def test_sort_by_timestamp(self):
        results = [
            _make_result(timestamp="2024-01-03T00:00:00"),
            _make_result(timestamp="2024-01-01T00:00:00"),
            _make_result(timestamp="2024-01-02T00:00:00"),
        ]
        out = sort_results(results, key=SortKey.TIMESTAMP, descending=False)
        assert out[0].entry.timestamp == "2024-01-01T00:00:00"
        assert out[-1].entry.timestamp == "2024-01-03T00:00:00"

    def test_does_not_mutate_original(self):
        results = [_make_result(duration_ms=d) for d in [300, 100, 200]]
        original_order = [r.entry.duration_ms for r in results]
        sort_results(results, key=SortKey.DURATION)
        assert [r.entry.duration_ms for r in results] == original_order

    def test_empty_list(self):
        assert sort_results([], key=SortKey.DURATION) == []
