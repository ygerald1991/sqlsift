"""Tests for sqlsift.cost_estimator."""

from __future__ import annotations

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.cost_estimator import (
    CostEstimate,
    estimate_cost,
    estimate_costs,
    _duration_component,
    _suggestion_component,
    _severity_component,
)
from sqlsift.parser import QueryEntry
from sqlsift.scorer import Severity, ScoredResult


def _make_entry(query: str = "SELECT 1", duration_ms: float = 500.0) -> QueryEntry:
    return QueryEntry(timestamp="2024-01-01T00:00:00", duration_ms=duration_ms, query=query)


def _make_scored(
    query: str = "SELECT 1",
    duration_ms: float = 500.0,
    suggestions: list[str] | None = None,
    severity: Severity = Severity.LOW,
    score: float = 10.0,
) -> ScoredResult:
    entry = _make_entry(query, duration_ms)
    result = AnalysisResult(entry=entry, suggestions=suggestions or [])
    return ScoredResult(result=result, score=score, severity=severity)


class TestDurationComponent:
    def test_zero_duration_gives_zero(self):
        assert _duration_component(0.0) == 0.0

    def test_max_duration_gives_hundred(self):
        assert _duration_component(30_000.0) == 100.0

    def test_half_duration_gives_fifty(self):
        assert _duration_component(15_000.0) == pytest.approx(50.0)

    def test_over_max_clamped(self):
        assert _duration_component(99_999.0) == 100.0


class TestSuggestionComponent:
    def test_zero_suggestions_gives_zero(self):
        assert _suggestion_component(0) == 0.0

    def test_max_suggestions_gives_hundred(self):
        assert _suggestion_component(5) == 100.0

    def test_over_max_clamped(self):
        assert _suggestion_component(100) == 100.0


class TestSeverityComponent:
    def test_low_gives_zero(self):
        assert _severity_component(Severity.LOW) == 0.0

    def test_critical_gives_hundred(self):
        assert _severity_component(Severity.CRITICAL) == 100.0

    def test_medium_between_low_and_high(self):
        med = _severity_component(Severity.MEDIUM)
        high = _severity_component(Severity.HIGH)
        assert 0.0 < med < high < 100.0


class TestEstimateCost:
    def test_returns_cost_estimate_instance(self):
        scored = _make_scored()
        result = estimate_cost(scored)
        assert isinstance(result, CostEstimate)

    def test_query_preserved(self):
        scored = _make_scored(query="SELECT id FROM users")
        result = estimate_cost(scored)
        assert result.query == "SELECT id FROM users"

    def test_zero_inputs_give_zero_cost(self):
        scored = _make_scored(duration_ms=0.0, suggestions=[], severity=Severity.LOW)
        result = estimate_cost(scored)
        assert result.cost_score == 0.0

    def test_breakdown_keys_present(self):
        scored = _make_scored()
        result = estimate_cost(scored)
        assert set(result.breakdown.keys()) == {"duration", "suggestions", "severity"}

    def test_cost_score_bounded(self):
        scored = _make_scored(
            duration_ms=30_000.0,
            suggestions=["a", "b", "c", "d", "e"],
            severity=Severity.CRITICAL,
            score=100.0,
        )
        result = estimate_cost(scored)
        assert 0.0 <= result.cost_score <= 100.0


class TestEstimateCosts:
    def test_empty_input_returns_empty_list(self):
        assert estimate_costs([]) == []

    def test_sorted_by_cost_descending(self):
        low = _make_scored(duration_ms=100.0, severity=Severity.LOW)
        high = _make_scored(duration_ms=20_000.0, severity=Severity.CRITICAL,
                            suggestions=["x", "y", "z"])
        results = estimate_costs([low, high])
        assert results[0].cost_score >= results[1].cost_score

    def test_single_item_list(self):
        scored = _make_scored()
        results = estimate_costs([scored])
        assert len(results) == 1
