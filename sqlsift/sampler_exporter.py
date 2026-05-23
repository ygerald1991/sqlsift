"""sampler_exporter.py — JSON / CSV export for SampleReport."""
from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List

from sqlsift.query_sampler import SampleReport


def _result_to_dict(result: Any) -> Dict[str, Any]:  # AnalysisResult
    return {
        "query": result.entry.query,
        "duration_ms": result.entry.duration_ms,
        "is_slow": result.is_slow,
        "suggestions": result.suggestions,
    }


def export_sample_json(report: SampleReport) -> str:
    """Serialise the sample report to a JSON string."""
    payload: Dict[str, Any] = {
        "total_seen": report.total_seen,
        "sample_size": report.sample_size,
        "count": report.count,
        "coverage_ratio": report.coverage_ratio,
        "results": [_result_to_dict(r) for r in report.results],
    }
    return json.dumps(payload, indent=2)


def export_sample_csv(report: SampleReport) -> str:
    """Serialise the sample report to a CSV string."""
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=["query", "duration_ms", "is_slow", "suggestions"],
        lineterminator="\n",
    )
    writer.writeheader()
    for r in report.results:
        d = _result_to_dict(r)
        d["suggestions"] = "|".join(d["suggestions"])
        writer.writerow(d)
    return buf.getvalue()


def export_sample(report: SampleReport, fmt: str = "json") -> str:
    """Dispatch to the appropriate exporter based on *fmt*."""
    if fmt == "csv":
        return export_sample_csv(report)
    return export_sample_json(report)
