"""Export heatmap data to JSON and CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List

from sqlsift.heatmap import DAYS, HOURS, Heatmap, HeatmapCell


def _cell_to_dict(cell: HeatmapCell) -> Dict[str, Any]:
    return {
        "day": cell.day,
        "hour": cell.hour,
        "count": cell.count,
        "total_duration_ms": round(cell.total_duration, 3),
        "avg_duration_ms": round(cell.avg_duration, 3),
    }


def export_heatmap_json(heatmap: Heatmap) -> str:
    """Serialise the full heatmap to a JSON string."""
    rows: List[Dict[str, Any]] = []
    for day in DAYS:
        for h in HOURS:
            cell = heatmap.cells.get(day, {}).get(h, HeatmapCell(day=day, hour=h))
            rows.append(_cell_to_dict(cell))
    return json.dumps(rows, indent=2)


def export_heatmap_csv(heatmap: Heatmap) -> str:
    """Serialise the full heatmap to a CSV string."""
    buf = io.StringIO()
    fieldnames = ["day", "hour", "count", "total_duration_ms", "avg_duration_ms"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for day in DAYS:
        for h in HOURS:
            cell = heatmap.cells.get(day, {}).get(h, HeatmapCell(day=day, hour=h))
            writer.writerow(_cell_to_dict(cell))
    return buf.getvalue()
