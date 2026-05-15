"""Human-readable formatting for TrendReport."""

from __future__ import annotations

from typing import List

from sqlsift.trend import TrendEntry, TrendReport

_MAX_QUERY_LEN = 60


def _truncate(text: str, max_len: int = _MAX_QUERY_LEN) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def format_trend_entry(entry: TrendEntry) -> str:
    """Format a single TrendEntry as a multi-line string."""
    lines: List[str] = []
    query_display = _truncate(entry.query)
    direction = "(stable)"
    if entry.is_degrading():
        direction = "(degrading ↑)"
    elif entry.is_improving():
        direction = "(improving ↓)"
    lines.append(f"Query: {query_display}  {direction}")
    for point in entry.points:
        lines.append(
            f"  [{point.run_id}] avg={point.avg_duration:.1f}ms  "
            f"slow_ratio={point.slow_ratio:.0%}  n={point.sample_count}"
        )
    delta = entry.delta()
    if delta is not None:
        sign = "+" if delta >= 0 else ""
        lines.append(f"  Delta: {sign}{delta:.1f}ms")
    return "\n".join(lines)


def format_trend_report(report: TrendReport) -> str:
    """Format the full TrendReport as a human-readable string."""
    if not report.entries:
        return "No trend data available."
    sections: List[str] = []
    sections.append(f"=== Trend Report ({len(report.entries)} queries) ===")
    degrading = report.degrading()
    improving = report.improving()
    sections.append(
        f"Degrading: {len(degrading)}  Improving: {len(improving)}  "
        f"Stable: {len(report.entries) - len(degrading) - len(improving)}"
    )
    sections.append("")
    for entry in report.entries.values():
        sections.append(format_trend_entry(entry))
        sections.append("")
    return "\n".join(sections).rstrip()
