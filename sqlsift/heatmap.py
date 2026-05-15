"""Heatmap: bucket slow queries by hour-of-day and day-of-week."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from sqlsift.analyzer import AnalysisResult

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
HOURS = list(range(24))


@dataclass
class HeatmapCell:
    day: str
    hour: int
    count: int = 0
    total_duration: float = 0.0

    @property
    def avg_duration(self) -> float:
        return self.total_duration / self.count if self.count else 0.0


@dataclass
class Heatmap:
    # cells[day][hour] -> HeatmapCell
    cells: Dict[str, Dict[int, HeatmapCell]] = field(default_factory=dict)

    def get(self, day: str, hour: int) -> HeatmapCell:
        return self.cells.get(day, {}).get(hour, HeatmapCell(day=day, hour=hour))


def build_heatmap(results: Sequence[AnalysisResult]) -> Heatmap:
    """Build a heatmap of slow query counts from analysis results."""
    cells: Dict[str, Dict[int, HeatmapCell]] = {
        day: {h: HeatmapCell(day=day, hour=h) for h in HOURS} for day in DAYS
    }

    for result in results:
        if not result.is_slow:
            continue
        ts = result.entry.timestamp
        if ts is None:
            continue
        day = DAYS[ts.weekday()]
        hour = ts.hour
        cell = cells[day][hour]
        cell.count += 1
        cell.total_duration += result.entry.duration

    return Heatmap(cells=cells)


def peak_cells(heatmap: Heatmap, top_n: int = 5) -> List[HeatmapCell]:
    """Return the top_n cells with the highest slow-query count."""
    all_cells: List[HeatmapCell] = [
        cell
        for day_cells in heatmap.cells.values()
        for cell in day_cells.values()
        if cell.count > 0
    ]
    return sorted(all_cells, key=lambda c: c.count, reverse=True)[:top_n]
