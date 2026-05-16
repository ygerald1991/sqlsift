"""Format execution tracking reports for display."""
from __future__ import annotations

from typing import List

from sqlsift.execution_tracker import ExecutionRecord, ExecutionReport

_MAX_QUERY_LEN = 60


def _truncate(text: str, max_len: int = _MAX_QUERY_LEN) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def format_record(record: ExecutionRecord) -> str:
    query = _truncate(record.query_pattern)
    lines = [
        f"  Query : {query}",
        f"  Calls : {record.call_count}",
        f"  Avg   : {record.avg_duration:.1f}ms",
        f"  Max   : {record.max_duration:.1f}ms",
        f"  Min   : {record.min_duration:.1f}ms",
    ]
    return "\n".join(lines)


def format_execution_report(
    report: ExecutionReport,
    top_n: int = 5,
) -> str:
    sections: List[str] = []
    sections.append(
        f"=== Execution Tracker ==="
        f"  Total queries : {report.total_queries}"
        f"  Unique patterns: {report.unique_patterns}"
    )
    sections.append("\n--- Most Frequent Queries ---")
    for rec in report.most_frequent(top_n):
        sections.append(format_record(rec))
        sections.append("")

    sections.append("--- Slowest Queries (avg) ---")
    for rec in report.slowest_avg(top_n):
        sections.append(format_record(rec))
        sections.append("")

    return "\n".join(sections)
