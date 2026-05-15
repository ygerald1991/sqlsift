"""Tests for sqlsift.trend_formatter."""

from __future__ import annotations

from sqlsift.trend import TrendEntry, TrendPoint, TrendReport
from sqlsift.trend_formatter import (
    _truncate,
    format_trend_entry,
    format_trend_report,
)


class TestTruncate:
    def test_short_string_unchanged(self):
        assert _truncate("SELECT 1") == "SELECT 1"

    def test_long_string_truncated(self):
        long = "A" * 80
        result = _truncate(long)
        assert result.endswith("...")
        assert len(result) == 60

    def test_exactly_max_len_unchanged(self):
        exact = "B" * 60
        assert _truncate(exact) == exact


class TestFormatTrendEntry:
    def _make_entry(self, durations: list[float]) -> TrendEntry:
        points = [
            TrendPoint(run_id=f"r{i+1}", avg_duration=d, slow_ratio=0.5, sample_count=5)
            for i, d in enumerate(durations)
        ]
        return TrendEntry(query="SELECT id FROM users", points=points)

    def test_single_point_shows_stable(self):
        entry = self._make_entry([100.0])
        text = format_trend_entry(entry)
        assert "(stable)" in text

    def test_degrading_label_shown(self):
        entry = self._make_entry([50.0, 200.0])
        text = format_trend_entry(entry)
        assert "degrading" in text

    def test_improving_label_shown(self):
        entry = self._make_entry([200.0, 50.0])
        text = format_trend_entry(entry)
        assert "improving" in text

    def test_run_ids_appear_in_output(self):
        entry = self._make_entry([100.0, 150.0])
        text = format_trend_entry(entry)
        assert "[r1]" in text
        assert "[r2]" in text

    def test_delta_shown_for_multiple_points(self):
        entry = self._make_entry([100.0, 250.0])
        text = format_trend_entry(entry)
        assert "Delta" in text
        assert "+150.0ms" in text

    def test_no_delta_for_single_point(self):
        entry = self._make_entry([100.0])
        text = format_trend_entry(entry)
        assert "Delta" not in text


class TestFormatTrendReport:
    def test_empty_report_returns_message(self):
        report = TrendReport()
        text = format_trend_report(report)
        assert "No trend data" in text

    def test_report_header_present(self):
        entry = TrendEntry(
            query="SELECT 1",
            points=[TrendPoint("r1", 100.0, 0.5, 3)],
        )
        report = TrendReport(entries={"SELECT 1": entry})
        text = format_trend_report(report)
        assert "Trend Report" in text

    def test_counts_in_header(self):
        e1 = TrendEntry(
            query="SELECT 1",
            points=[
                TrendPoint("r1", 50.0, 0.1, 3),
                TrendPoint("r2", 200.0, 0.8, 3),
            ],
        )
        e2 = TrendEntry(
            query="SELECT 2",
            points=[
                TrendPoint("r1", 200.0, 0.8, 3),
                TrendPoint("r2", 50.0, 0.1, 3),
            ],
        )
        report = TrendReport(entries={"SELECT 1": e1, "SELECT 2": e2})
        text = format_trend_report(report)
        assert "Degrading: 1" in text
        assert "Improving: 1" in text
