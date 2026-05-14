"""Formatting helpers for ProfileEntry objects."""

from __future__ import annotations

from typing import Dict, List

from sqlsift.profiler import ProfileEntry

_TRUNCATE_LEN = 72


def _truncate(text: str, max_len: int = _TRUNCATE_LEN) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def format_profile_entry(entry: ProfileEntry) -> str:
    """Return a human-readable summary for a single ProfileEntry."""
    lines = [
        f"Pattern : {_truncate(entry.pattern)}",
        f"Executions : {entry.executions}",
        f"Avg Duration : {entry.avg_duration:.3f}s",
        f"Min / Max : {entry.min_duration:.3f}s / {entry.max_duration:.3f}s",
        f"Total Duration : {entry.total_duration:.3f}s",
        f"Slow Ratio : {entry.slow_ratio:.1%} ({entry.slow_count}/{entry.executions})",
    ]
    if entry.unique_suggestions:
        lines.append("Suggestions:")
        for suggestion in entry.unique_suggestions:
            lines.append(f"  - {suggestion}")
    return "\n".join(lines)


def format_profile_report(profiles: Dict[str, ProfileEntry], top_n: int = 5) -> str:
    """Return a formatted report of the top-n slowest query patterns."""
    from sqlsift.profiler import top_patterns_by_total_time

    if not profiles:
        return "No query profiles available."

    top = top_patterns_by_total_time(profiles, n=top_n)
    sections: List[str] = [
        f"=== Top {len(top)} Query Patterns by Total Duration ==="
    ]

    for rank, entry in enumerate(top, start=1):
        sections.append(f"\n[#{rank}]")
        sections.append(format_profile_entry(entry))

    total_exec = sum(e.executions for e in profiles.values())
    total_time = sum(e.total_duration for e in profiles.values())
    sections.append(
        f"\nSummary: {len(profiles)} unique pattern(s), "
        f"{total_exec} total execution(s), "
        f"{total_time:.3f}s total time."
    )
    return "\n".join(sections)
