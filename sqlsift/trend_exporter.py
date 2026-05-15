"""Export TrendReport to JSON and CSV formats."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List

from sqlsift.trend import TrendReport


def trend_entry_to_dict(query: str, entry_data: Any) -> Dict[str, Any]:
    """Convert a TrendEntry to a serialisable dict."""
    return {
        "query": query,
        "is_improving": entry_data.is_improving(),
        "is_degrading": entry_data.is_degrading(),
        "delta_ms": entry_data.delta(),
        "points": [
            {
                "run_id": p.run_id,
                "avg_duration": p.avg_duration,
                "slow_ratio": p.slow_ratio,
                "sample_count": p.sample_count,
            }
            for p in entry_data.points
        ],
    }


def export_trend_json(report: TrendReport, indent: int = 2) -> str:
    """Serialise a TrendReport to a JSON string."""
    data: List[Dict[str, Any]] = [
        trend_entry_to_dict(q, e) for q, e in report.entries.items()
    ]
    return json.dumps(data, indent=indent)


def export_trend_csv(report: TrendReport) -> str:
    """Serialise a TrendReport to a flat CSV string (one row per point)."""
    output = io.StringIO()
    fieldnames = [
        "query",
        "run_id",
        "avg_duration",
        "slow_ratio",
        "sample_count",
        "is_degrading",
        "is_improving",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for query, entry in report.entries.items():
        for point in entry.points:
            writer.writerow(
                {
                    "query": query,
                    "run_id": point.run_id,
                    "avg_duration": point.avg_duration,
                    "slow_ratio": point.slow_ratio,
                    "sample_count": point.sample_count,
                    "is_degrading": entry.is_degrading(),
                    "is_improving": entry.is_improving(),
                }
            )
    return output.getvalue()
