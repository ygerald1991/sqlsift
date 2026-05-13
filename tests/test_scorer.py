"""Tests for sqlsift.scorer."""

import pytest
from sqlsift.analyzer import AnalysisResult
from sqlsift.scorer import (
    Severity,
    ScoredResult,
    compute_score,
    classify_severity,
    score_result,
    score_results,
)


def _make_result(duration_ms: float, suggestions=None) -> AnalysisResult:
    suggestions = suggestions or []
    return AnalysisResult(
        query="SELECT 1",
        duration_ms=duration_ms,
        is_slow=duration_ms >= 1000,
        suggestions=suggestions,
    )


class TestComputeScore:
    def test_zero_duration_no_suggestions_gives_zero(self):
        result = _make_result(0.0, [])
        assert compute_score(result) == 0

    def test_max_duration_no_suggestions_gives_sixty(self):
        result = _make_result(5000.0, [])
        assert compute_score(result) == 60

    def test_zero_duration_max_suggestions_gives_forty(self):
        result = _make_result(0.0, ["a", "b", "c", "d", "e"])
        assert compute_score(result) == 40

    def test_score_capped_at_100(self):
        result = _make_result(99999.0, ["a", "b", "c", "d", "e"])
        assert compute_score(result) == 100

    def test_partial_score(self):
        result = _make_result(2500.0, ["a"])
        score = compute_score(result)
        assert 0 < score < 100


class TestClassifySeverity:
    def test_score_0_is_low(self):
        assert classify_severity(0) == Severity.LOW

    def test_score_24_is_low(self):
        assert classify_severity(24) == Severity.LOW

    def test_score_25_is_medium(self):
        assert classify_severity(25) == Severity.MEDIUM

    def test_score_49_is_medium(self):
        assert classify_severity(49) == Severity.MEDIUM

    def test_score_50_is_high(self):
        assert classify_severity(50) == Severity.HIGH

    def test_score_80_is_critical(self):
        assert classify_severity(80) == Severity.CRITICAL

    def test_score_100_is_critical(self):
        assert classify_severity(100) == Severity.CRITICAL


class TestScoreResult:
    def test_returns_scored_result(self):
        result = _make_result(1000.0, ["use index"])
        scored = score_result(result)
        assert isinstance(scored, ScoredResult)
        assert scored.result is result

    def test_score_and_severity_consistent(self):
        result = _make_result(4000.0, ["a", "b", "c"])
        scored = score_result(result)
        assert scored.severity == classify_severity(scored.score)


class TestScoreResults:
    def test_empty_list(self):
        assert score_results([]) == []

    def test_sorted_highest_first(self):
        results = [
            _make_result(100.0, []),
            _make_result(4000.0, ["a", "b", "c"]),
            _make_result(1500.0, ["x"]),
        ]
        scored = score_results(results)
        scores = [s.score for s in scored]
        assert scores == sorted(scores, reverse=True)

    def test_all_results_present(self):
        results = [_make_result(float(i * 500)) for i in range(4)]
        scored = score_results(results)
        assert len(scored) == 4
