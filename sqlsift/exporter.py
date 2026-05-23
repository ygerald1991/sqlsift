"""Export analysis results to various output formats (JSON, CSV)."""

from __future__ import annotations

import csv
import io
import json
from typing import List

from sqlsift.analyzer import AnalysisResult


def result_to_dict(result: AnalysisResult) -> dict:
    """Convert an AnalysisResult to a plain dictionary."""
    return {
        "query": result.entry.query,
        "duration_ms": result.entry.duration_ms,
        "timestamp": result.entry.timestamp,
        "is_slow": result.is_slow,
        "suggestions": result.suggestions,
    }


def export_json(results: List[AnalysisResult], indent: int = 2) -> str:
    """Serialize a list of AnalysisResult objects to a JSON string."""
    return json.dumps([result_to_dict(r) for r in results], indent=indent, default=str)


def export_csv(results: List[AnalysisResult]) -> str:
    """Serialize a list of AnalysisResult objects to a CSV string.

    Multiple suggestions for a single entry are joined with a pipe ('|') character.
    """
    fieldnames = ["timestamp", "duration_ms", "is_slow", "suggestions", "query"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for result in results:
        row = result_to_dict(result)
        row["suggestions"] = " | ".join(row["suggestions"])
        writer.writerow(row)
    return output.getvalue()


def export_results(results: List[AnalysisResult], fmt: str = "json") -> str:
    """Export results in the requested format.

    Args:
        results: List of AnalysisResult objects to export.
        fmt: Output format — 'json' or 'csv'.

    Returns:
        Formatted string representation of the results.

    Raises:
        ValueError: If an unsupported format is requested.
        TypeError: If results is not a list.
    """
    if not isinstance(results, list):
        raise TypeError(f"Expected a list of AnalysisResult objects, got {type(results).__name__!r}.")
    fmt = fmt.lower()
    if fmt == "json":
        return export_json(results)
    if fmt == "csv":
        return export_csv(results)
    raise ValueError(f"Unsupported export format: {fmt!r}. Choose 'json' or 'csv'.")
