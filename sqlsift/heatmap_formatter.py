"""Text formatter for Heatmap output."""
from __future__ import annotations

from sqlsift.heatmap import DAYS, HOURS, Heatmap, HeatmapCell, peak_cells

_COL_W = 6


def _bar(count: int, max_count: int, width: int = 4) -> str:
    if max_count == 0:
        return " " * width
    filled = round(count / max_count * width)
    return ("#" * filled).ljust(width)


def format_heatmap(heatmap: Heatmap) -> str:
    """Render a compact ASCII heatmap (days x hours)."""
    max_count = max(
        (cell.count for day_cells in heatmap.cells.values() for cell in day_cells.values()),
        default=0,
    )

    header = "    " + "".join(f"{h:>{_COL_W}}" for h in HOURS)
    lines = ["Slow Query Heatmap (count per hour)", header]

    for day in DAYS:
        row_parts = [f"{day:<4}"]
        for h in HOURS:
            cell = heatmap.cells.get(day, {}).get(h, HeatmapCell(day=day, hour=h))
            row_parts.append(f"{cell.count:>{_COL_W}}")
        lines.append("".join(row_parts))

    return "\n".join(lines)


def format_peak_cells(heatmap: Heatmap, top_n: int = 5) -> str:
    """Render a short list of the busiest day/hour slots."""
    peaks = peak_cells(heatmap, top_n=top_n)
    if not peaks:
        return "No slow queries recorded."

    lines = [f"Top {top_n} peak slots:"]
    for i, cell in enumerate(peaks, 1):
        lines.append(
            f"  {i}. {cell.day} {cell.hour:02d}:00 — "
            f"{cell.count} slow queries, "
            f"avg {cell.avg_duration:.1f}ms"
        )
    return "\n".join(lines)
