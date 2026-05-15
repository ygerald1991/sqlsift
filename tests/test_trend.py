"""Tests for sqlsift.trend."""

from __future__ import annotations

from sqlsift.baseline import Baseline, BaselineEntry
from sqlsift.trend import TrendEntry, TrendPoint, build_trend


def _make_baseline(data: dict[str, tuple[float, float, int]]) -> Baseline:
    entries = {
        q: BaselineEntry(
            query=q,
            avg_duration=avg,
            slow_ratio=sr,
            sample_count=n,
        )
        for q, (avg, sr, n) in data.items()
    }
    return Baseline(entries=entries)


class TestTrendEntry:
    def test_single_point_not_improving_or_degrading(self):
        entry = TrendEntry(query="SELECT 1", points=[TrendPoint("r1", 100.0, 0.5, 10)])
        assert not entry.is_improving()
        assert not entry.is_degrading()

    def test_delta_none_with_single_point(self):
        entry = TrendEntry(query="SELECT 1", points=[TrendPoint("r1", 100.0, 0.5, 10)])
        assert entry.delta() is None

    def test_degrading_detected(self):
        entry = TrendEntry(
            query="SELECT 1",
            points=[
                TrendPoint("r1", 50.0, 0.1, 5),
                TrendPoint("r2", 150.0, 0.5, 5),
            ],
        )
        assert entry.is_degrading()
        assert not entry.is_improving()

    def test_improving_detected(self):
        entry = TrendEntry(
            query="SELECT 1",
            points=[
                TrendPoint("r1", 200.0, 0.8, 5),
                TrendPoint("r2", 80.0, 0.2, 5),
            ],
        )
        assert entry.is_improving()
        assert not entry.is_degrading()

    def test_delta_positive_when_degrading(self):
        entry = TrendEntry(
            query="SELECT 1",
            points=[
                TrendPoint("r1", 100.0, 0.3, 3),
                TrendPoint("r2", 250.0, 0.7, 3),
            ],
        )
        assert entry.delta() == 150.0

    def test_delta_negative_when_improving(self):
        entry = TrendEntry(
            query="SELECT 1",
            points=[
                TrendPoint("r1", 300.0, 0.9, 3),
                TrendPoint("r2", 100.0, 0.1, 3),
            ],
        )
        assert entry.delta() == -200.0


class TestBuildTrend:
    def test_empty_runs_returns_empty_report(self):
        report = build_trend([])
        assert report.entries == {}

    def test_single_run_creates_entries(self):
        b = _make_baseline({"SELECT 1": (100.0, 0.5, 10)})
        report = build_trend([("run1", b)])
        assert "SELECT 1" in report.entries
        assert len(report.entries["SELECT 1"].points) == 1

    def test_two_runs_merge_same_query(self):
        b1 = _make_baseline({"SELECT 1": (100.0, 0.4, 5)})
        b2 = _make_baseline({"SELECT 1": (200.0, 0.8, 5)})
        report = build_trend([("r1", b1), ("r2", b2)])
        entry = report.entries["SELECT 1"]
        assert len(entry.points) == 2
        assert entry.points[0].run_id == "r1"
        assert entry.points[1].run_id == "r2"

    def test_degrading_list_populated(self):
        b1 = _make_baseline({"SELECT 1": (50.0, 0.1, 3)})
        b2 = _make_baseline({"SELECT 1": (300.0, 0.9, 3)})
        report = build_trend([("r1", b1), ("r2", b2)])
        assert len(report.degrading()) == 1
        assert len(report.improving()) == 0

    def test_improving_list_populated(self):
        b1 = _make_baseline({"SELECT 1": (300.0, 0.9, 3)})
        b2 = _make_baseline({"SELECT 1": (50.0, 0.1, 3)})
        report = build_trend([("r1", b1), ("r2", b2)])
        assert len(report.improving()) == 1
        assert len(report.degrading()) == 0

    def test_multiple_queries_tracked_independently(self):
        b1 = _make_baseline({"SELECT 1": (100.0, 0.3, 5), "SELECT 2": (200.0, 0.6, 5)})
        b2 = _make_baseline({"SELECT 1": (90.0, 0.2, 5), "SELECT 2": (300.0, 0.9, 5)})
        report = build_trend([("r1", b1), ("r2", b2)])
        assert len(report.entries) == 2
        assert report.entries["SELECT 1"].is_improving()
        assert report.entries["SELECT 2"].is_degrading()
