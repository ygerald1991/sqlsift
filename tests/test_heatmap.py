"""Tests for sqlsift.heatmap."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.heatmap import DAYS, build_heatmap, peak_cells
from sqlsift.parser import QueryEntry


def _make_result(
    duration: float,
    is_slow: bool,
    timestamp: Optional[datetime] = None,
    query: str = "SELECT 1",
) -> AnalysisResult:
    entry = QueryEntry(
        timestamp=timestamp,
        duration=duration,
        query=query,
    )
    return AnalysisResult(entry=entry, is_slow=is_slow, suggestions=[])


class TestBuildHeatmap:
    def test_empty_input_produces_zero_cells(self):
        hm = build_heatmap([])
        for day in DAYS:
            for h in range(24):
                assert hm.cells[day][h].count == 0

    def test_fast_query_not_counted(self):
        ts = datetime(2024, 1, 1, 10, 0)  # Monday 10:00
        result = _make_result(50.0, is_slow=False, timestamp=ts)
        hm = build_heatmap([result])
        assert hm.cells["Mon"][10].count == 0

    def test_slow_query_without_timestamp_skipped(self):
        result = _make_result(500.0, is_slow=True, timestamp=None)
        hm = build_heatmap([result])
        total = sum(c.count for d in hm.cells.values() for c in d.values())
        assert total == 0

    def test_slow_query_counted_in_correct_cell(self):
        ts = datetime(2024, 1, 3, 14, 0)  # Wednesday 14:00
        result = _make_result(300.0, is_slow=True, timestamp=ts)
        hm = build_heatmap([result])
        assert hm.cells["Wed"][14].count == 1
        assert hm.cells["Wed"][14].total_duration == 300.0

    def test_multiple_slow_queries_same_cell_accumulated(self):
        ts = datetime(2024, 1, 5, 9, 0)  # Friday 09:00
        results = [
            _make_result(100.0, is_slow=True, timestamp=ts),
            _make_result(200.0, is_slow=True, timestamp=ts),
        ]
        hm = build_heatmap(results)
        cell = hm.cells["Fri"][9]
        assert cell.count == 2
        assert cell.avg_duration == pytest.approx(150.0)

    def test_get_returns_zero_cell_for_missing_key(self):
        hm = build_heatmap([])
        cell = hm.get("Mon", 0)
        assert cell.count == 0


class TestPeakCells:
    def test_empty_heatmap_returns_empty_list(self):
        hm = build_heatmap([])
        assert peak_cells(hm) == []

    def test_returns_at_most_top_n(self):
        results = [
            _make_result(100.0, is_slow=True, timestamp=datetime(2024, 1, 1 + i, i % 24, 0))
            for i in range(10)
        ]
        hm = build_heatmap(results)
        assert len(peak_cells(hm, top_n=3)) <= 3

    def test_highest_count_cell_first(self):
        ts_busy = datetime(2024, 1, 1, 8, 0)  # Mon 08
        ts_quiet = datetime(2024, 1, 2, 8, 0)  # Tue 08
        results = [
            _make_result(100.0, is_slow=True, timestamp=ts_busy),
            _make_result(100.0, is_slow=True, timestamp=ts_busy),
            _make_result(100.0, is_slow=True, timestamp=ts_quiet),
        ]
        hm = build_heatmap(results)
        peaks = peak_cells(hm, top_n=5)
        assert peaks[0].count == 2
