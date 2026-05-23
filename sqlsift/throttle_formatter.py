"""throttle_formatter.py – human-readable formatting for ThrottleReport."""
from __future__ import annotations

from sqlsift.query_throttler import ThrottleEntry, ThrottleReport

_MAX_QUERY_LEN = 72


def _truncate(text: str, max_len: int = _MAX_QUERY_LEN) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def format_throttle_entry(entry: ThrottleEntry) -> str:
    """Return a single-line summary for *entry*."""
    flag = "[FLAGGED]" if entry.flagged else "[ok]     "
    query = _truncate(entry.pattern)
    return (
        f"{flag} occurrences={entry.occurrences:>5}  "
        f"avg={entry.avg_duration_ms:>8.1f} ms  "
        f"query: {query}"
    )


def format_throttle_report(report: ThrottleReport) -> str:
    """Return a formatted multi-line string for *report*."""
    lines: list[str] = [
        "=== Query Throttle Report ===",
        f"Threshold : {report.threshold} occurrences",
        f"Patterns  : {report.count}",
        f"Flagged   : {len(report.flagged)}",
        "",
    ]

    if not report.entries:
        lines.append("  (no data)")
        return "\n".join(lines)

    for entry in report.entries:
        lines.append("  " + format_throttle_entry(entry))

    return "\n".join(lines)
