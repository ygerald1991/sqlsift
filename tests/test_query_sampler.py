"""Tests for sqlsift.query_sampler."""
from __future__ import annotations

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.query_sampler import SampleConfig, SampleReport, sample_results


def _make_result(
    query: str = "SELECT 1",
    duration_ms: float = 50.0,
    is_slow: bool = False,
    suggestions: list[str] | None = None,
) -> AnalysisResult:
    entry = QueryEntry(
        timestamp="2024-01-01T00:00:00",
        duration_ms=duration_ms,
        query=query,
        user="test",
        database="db",
    )
    return AnalysisResult(
        entry=entry,
        is_slow=is_slow,
        suggestions=suggestions or [],
    )


class TestSampleResults:
    def test_empty_input_returns_empty_report(self):
        report = sample_results([])
        assert report.count == 0
        assert report.total_seen == 0
        assert report.coverage_ratio == 0.0

    def test_fewer_items_than_sample_size_returns_all(self):
        results = [_make_result() for _ in range(5)]
        report = sample_results(results, SampleConfig(sample_size=100))
        assert report.count == 5
        assert report.total_seen == 5

    def test_sample_size_limits_output(self):
        results = [_make_result() for _ in range(200)]
        report = sample_results(results, SampleConfig(sample_size=50, seed=42))
        assert report.count == 50
        assert report.total_seen == 200

    def test_coverage_ratio_computed_correctly(self):
        results = [_make_result() for _ in range(100)]
        report = sample_results(results, SampleConfig(sample_size=25, seed=0))
        assert report.coverage_ratio == pytest.approx(0.25, abs=1e-4)

    def test_slow_only_excludes_fast_queries(self):
        fast = [_make_result(is_slow=False) for _ in range(10)]
        slow = [_make_result(is_slow=True, duration_ms=2000.0) for _ in range(5)]
        report = sample_results(fast + slow, SampleConfig(slow_only=True, sample_size=100))
        assert report.total_seen == 5
        assert all(r.is_slow for r in report.results)

    def test_slow_only_with_no_slow_queries_returns_empty(self):
        results = [_make_result(is_slow=False) for _ in range(10)]
        report = sample_results(results, SampleConfig(slow_only=True))
        assert report.count == 0

    def test_seed_produces_deterministic_output(self):
        results = [_make_result(query=f"SELECT {i}") for i in range(500)]
        cfg = SampleConfig(sample_size=20, seed=7)
        report_a = sample_results(results, cfg)
        report_b = sample_results(results, cfg)
        queries_a = [r.entry.query for r in report_a.results]
        queries_b = [r.entry.query for r in report_b.results]
        assert queries_a == queries_b

    def test_different_seeds_likely_produce_different_output(self):
        results = [_make_result(query=f"SELECT {i}") for i in range(500)]
        report_a = sample_results(results, SampleConfig(sample_size=20, seed=1))
        report_b = sample_results(results, SampleConfig(sample_size=20, seed=999))
        queries_a = [r.entry.query for r in report_a.results]
        queries_b = [r.entry.query for r in report_b.results]
        assert queries_a != queries_b

    def test_default_config_used_when_none_provided(self):
        results = [_make_result() for _ in range(10)]
        report = sample_results(results)
        assert isinstance(report, SampleReport)
        assert report.count == 10
