"""Tests for sqlsift.profiler."""

from __future__ import annotations

from typing import List

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.profiler import ProfileEntry, profile_results, top_patterns_by_total_time


def _make_result(
    query: str,
    duration: float,
    is_slow: bool = False,
    suggestions: List[str] | None = None,
) -> AnalysisResult:
    entry = QueryEntry(timestamp="2024-01-01T00:00:00", query=query, duration=duration)
    return AnalysisResult(
        entry=entry,
        is_slow=is_slow,
        suggestions=suggestions or [],
    )


class TestProfileResults:
    def test_empty_input_returns_empty_dict(self):
        assert profile_results([]) == {}

    def test_single_result_creates_profile(self):
        result = _make_result("SELECT * FROM users", 1.5)
        profiles = profile_results([result])
        assert len(profiles) == 1
        entry = next(iter(profiles.values()))
        assert entry.executions == 1
        assert entry.total_duration == pytest.approx(1.5)
        assert entry.min_duration == pytest.approx(1.5)
        assert entry.max_duration == pytest.approx(1.5)

    def test_identical_queries_merged(self):
        results = [
            _make_result("SELECT * FROM users WHERE id = 1", 1.0),
            _make_result("SELECT * FROM users WHERE id = 2", 3.0),
        ]
        profiles = profile_results(results)
        assert len(profiles) == 1
        entry = next(iter(profiles.values()))
        assert entry.executions == 2
        assert entry.total_duration == pytest.approx(4.0)
        assert entry.min_duration == pytest.approx(1.0)
        assert entry.max_duration == pytest.approx(3.0)

    def test_different_queries_separate_profiles(self):
        results = [
            _make_result("SELECT * FROM users", 1.0),
            _make_result("SELECT * FROM orders", 2.0),
        ]
        profiles = profile_results(results)
        assert len(profiles) == 2

    def test_slow_count_tracked(self):
        results = [
            _make_result("SELECT * FROM users", 0.5, is_slow=False),
            _make_result("SELECT * FROM users", 2.0, is_slow=True),
            _make_result("SELECT * FROM users", 3.0, is_slow=True),
        ]
        profiles = profile_results(results)
        entry = next(iter(profiles.values()))
        assert entry.slow_count == 2

    def test_slow_ratio_calculated(self):
        results = [
            _make_result("SELECT id FROM t", 0.5, is_slow=False),
            _make_result("SELECT id FROM t", 2.0, is_slow=True),
        ]
        profiles = profile_results(results)
        entry = next(iter(profiles.values()))
        assert entry.slow_ratio == pytest.approx(0.5)

    def test_suggestions_collected(self):
        results = [
            _make_result("SELECT * FROM t", 1.0, suggestions=["Avoid SELECT *"]),
            _make_result("SELECT * FROM t", 1.0, suggestions=["Add index"]),
        ]
        profiles = profile_results(results)
        entry = next(iter(profiles.values()))
        assert "Avoid SELECT *" in entry.all_suggestions
        assert "Add index" in entry.all_suggestions

    def test_unique_suggestions_deduplicated(self):
        results = [
            _make_result("SELECT * FROM t", 1.0, suggestions=["Avoid SELECT *"]),
            _make_result("SELECT * FROM t", 1.0, suggestions=["Avoid SELECT *"]),
        ]
        profiles = profile_results(results)
        entry = next(iter(profiles.values()))
        assert entry.unique_suggestions == ["Avoid SELECT *"]

    def test_avg_duration(self):
        results = [
            _make_result("SELECT 1", 2.0),
            _make_result("SELECT 1", 4.0),
        ]
        profiles = profile_results(results)
        entry = next(iter(profiles.values()))
        assert entry.avg_duration == pytest.approx(3.0)


class TestTopPatternsByTotalTime:
    def test_returns_top_n(self):
        profiles = {
            "a": ProfileEntry(pattern="a", executions=1, total_duration=10.0),
            "b": ProfileEntry(pattern="b", executions=1, total_duration=5.0),
            "c": ProfileEntry(pattern="c", executions=1, total_duration=20.0),
        }
        top = top_patterns_by_total_time(profiles, n=2)
        assert len(top) == 2
        assert top[0].pattern == "c"
        assert top[1].pattern == "a"

    def test_fewer_than_n_returns_all(self):
        profiles = {
            "a": ProfileEntry(pattern="a", executions=1, total_duration=1.0),
        }
        top = top_patterns_by_total_time(profiles, n=5)
        assert len(top) == 1

    def test_empty_profiles_returns_empty(self):
        assert top_patterns_by_total_time({}, n=3) == []
