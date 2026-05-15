"""Format snapshot diffs and summaries for human-readable output."""
from __future__ import annotations

from typing import Dict

from sqlsift.snapshot import Snapshot, diff_snapshots

_SEP = "-" * 60


def _truncate(text: str, max_len: int = 60) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def format_snapshot_summary(snapshot: Snapshot) -> str:
    """Return a short human-readable summary of a single snapshot."""
    lines = [
        _SEP,
        f"Snapshot : {snapshot.label or '(unlabeled)'}" ,
        f"Timestamp: {snapshot.timestamp}",
        f"Queries  : {snapshot.query_count}",
        f"Slow     : {snapshot.slow_count}",
        _SEP,
    ]
    return "\n".join(lines)


def format_diff(diff: Dict) -> str:
    """Render a snapshot diff dict as a readable report."""
    lines = [
        _SEP,
        "Snapshot Diff",
        _SEP,
        f"Slow queries before : {diff['slow_count_before']}",
        f"Slow queries after  : {diff['slow_count_after']}",
    ]

    if diff["added_queries"]:
        lines.append("\nAdded queries:")
        for q in diff["added_queries"]:
            lines.append(f"  + {_truncate(q)}")

    if diff["removed_queries"]:
        lines.append("\nRemoved queries:")
        for q in diff["removed_queries"]:
            lines.append(f"  - {_truncate(q)}")

    if diff["newly_slow_queries"]:
        lines.append("\nNewly slow queries:")
        for q in diff["newly_slow_queries"]:
            lines.append(f"  ! {_truncate(q)}")

    if not any([
        diff["added_queries"],
        diff["removed_queries"],
        diff["newly_slow_queries"],
    ]):
        lines.append("\nNo notable changes detected.")

    lines.append(_SEP)
    return "\n".join(lines)


def format_snapshot_diff(before: Snapshot, after: Snapshot) -> str:
    """Convenience wrapper: diff two snapshots and return formatted output."""
    diff = diff_snapshots(before, after)
    header = [
        f"Before: {before.label or '(unlabeled)'}  [{before.timestamp}]",
        f"After : {after.label or '(unlabeled)'}  [{after.timestamp}]",
        "",
    ]
    return "\n".join(header) + format_diff(diff)
