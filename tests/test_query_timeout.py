"""Tests for sqlsift.query_timeout."""
from __future__ import annotations

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.scorer import Severity, ScoredResult
from sqlsift.query_timeout import (
    TimeoutConfig,
    TimeoutFlag,
    TimeoutReport,
    check_timeout,
    build_timeout_report,
)


def _make_scored(query: str = "SELECT 1", duration_ms: float = 100.0) -> ScoredResult:
    entry = QueryEntry(timestamp="2024-01-01T00:00:00", duration_ms=duration_ms, query=query)
    result = AnalysisResult(entry=entry, is_slow=duration_ms >= 1000, suggestions=[])
    return ScoredResult(result=result, score=duration_ms / 100, severity=Severity.LOW)


class TestTimeoutConfig:
    def test_default_timeout(self):
        cfg = TimeoutConfig()
        assert cfg.timeout_ms == 5_000.0

    def test_warning_threshold_is_ratio_of_timeout(self):
        cfg = TimeoutConfig(timeout_ms=4_000.0, warning_ratio=0.5)
        assert cfg.warning_threshold() == 2_000.0

    def test_custom_values_preserved(self):
        cfg = TimeoutConfig(timeout_ms=1_000.0, warning_ratio=0.8)
        assert cfg.warning_threshold() == 800.0


class TestCheckTimeout:
    def test_fast_query_returns_none(self):
        scored = _make_scored(duration_ms=100.0)
        assert check_timeout(scored) is None

    def test_near_timeout_returns_flag(self):
        cfg = TimeoutConfig(timeout_ms=1_000.0, warning_ratio=0.75)
        scored = _make_scored(duration_ms=800.0)
        flag = check_timeout(scored, cfg)
        assert flag is not None
        assert flag.near_timeout is True
        assert flag.exceeded is False

    def test_exceeded_timeout_returns_flag(self):
        cfg = TimeoutConfig(timeout_ms=1_000.0)
        scored = _make_scored(duration_ms=1_500.0)
        flag = check_timeout(scored, cfg)
        assert flag is not None
        assert flag.exceeded is True

    def test_exactly_at_timeout_is_exceeded(self):
        cfg = TimeoutConfig(timeout_ms=1_000.0)
        scored = _make_scored(duration_ms=1_000.0)
        flag = check_timeout(scored, cfg)
        assert flag is not None
        assert flag.exceeded is True

    def test_exactly_at_warning_threshold_flagged(self):
        cfg = TimeoutConfig(timeout_ms=1_000.0, warning_ratio=0.75)
        scored = _make_scored(duration_ms=750.0)
        flag = check_timeout(scored, cfg)
        assert flag is not None
        assert flag.near_timeout is True

    def test_severity_critical_when_exceeded(self):
        cfg = TimeoutConfig(timeout_ms=500.0)
        scored = _make_scored(duration_ms=600.0)
        flag = check_timeout(scored, cfg)
        assert flag.severity == Severity.CRITICAL

    def test_severity_high_when_near(self):
        cfg = TimeoutConfig(timeout_ms=1_000.0, warning_ratio=0.75)
        scored = _make_scored(duration_ms=800.0)
        flag = check_timeout(scored, cfg)
        assert flag.severity == Severity.HIGH

    def test_message_contains_exceeded_text(self):
        cfg = TimeoutConfig(timeout_ms=1_000.0)
        scored = _make_scored(duration_ms=1_200.0)
        flag = check_timeout(scored, cfg)
        assert "exceeded" in flag.message.lower()

    def test_message_contains_near_text(self):
        cfg = TimeoutConfig(timeout_ms=1_000.0, warning_ratio=0.75)
        scored = _make_scored(duration_ms=800.0)
        flag = check_timeout(scored, cfg)
        assert "near" in flag.message.lower()


class TestBuildTimeoutReport:
    def test_empty_input_returns_empty_report(self):
        report = build_timeout_report([])
        assert report.count == 0

    def test_only_slow_queries_flagged(self):
        cfg = TimeoutConfig(timeout_ms=1_000.0, warning_ratio=0.75)
        results = [
            _make_scored(duration_ms=100.0),
            _make_scored(duration_ms=800.0),
            _make_scored(duration_ms=1_200.0),
        ]
        report = build_timeout_report(results, cfg)
        assert report.count == 2

    def test_exceeded_count_correct(self):
        cfg = TimeoutConfig(timeout_ms=1_000.0, warning_ratio=0.75)
        results = [
            _make_scored(duration_ms=800.0),
            _make_scored(duration_ms=1_200.0),
            _make_scored(duration_ms=1_500.0),
        ]
        report = build_timeout_report(results, cfg)
        assert report.exceeded_count == 2

    def test_near_count_excludes_exceeded(self):
        cfg = TimeoutConfig(timeout_ms=1_000.0, warning_ratio=0.75)
        results = [
            _make_scored(duration_ms=800.0),
            _make_scored(duration_ms=1_200.0),
        ]
        report = build_timeout_report(results, cfg)
        assert report.near_count == 1
        assert report.exceeded_count == 1
