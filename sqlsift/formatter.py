"""Formatter utilities for rendering aggregation summaries as human-readable text."""

from typing import Optional
from sqlsift.aggregator import AggregationSummary, QueryGroup

_HEADER = "=" * 60
_DIVIDER = "-" * 60


def _truncate(text: str, max_len: int = 55) -> str:
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def format_group(group: QueryGroup, rank: Optional[int] = None) -> str:
    """Format a single QueryGroup as a readable block."""
    lines = []
    prefix = f"#{rank} " if rank is not None else ""
    lines.append(f"{prefix}Pattern: {_truncate(group.pattern)}")
    lines.append(f"  Occurrences : {group.count}")
    lines.append(f"  Slow count  : {group.slow_count}")
    lines.append(f"  Avg duration: {group.avg_duration:.2f} ms")
    lines.append(f"  Max duration: {group.max_duration:.2f} ms")
    lines.append(f"  Total time  : {group.total_duration:.2f} ms")
    return "\n".join(lines)


def format_summary(summary: AggregationSummary, top_n: int = 5) -> str:
    """Format an AggregationSummary as a full report string."""
    lines = [_HEADER]
    lines.append("SQLSift Aggregation Summary")
    lines.append(_HEADER)
    lines.append(f"Total queries   : {summary.total_queries}")
    lines.append(f"Slow queries    : {summary.total_slow}")
    lines.append(f"Slow ratio      : {summary.slow_ratio:.1%}")
    lines.append(f"Unique patterns : {summary.unique_patterns}")
    lines.append(_DIVIDER)
    lines.append(f"Top {top_n} patterns by total duration:")
    lines.append(_DIVIDER)
    for rank, group in enumerate(summary.groups[:top_n], start=1):
        lines.append(format_group(group, rank=rank))
        lines.append(_DIVIDER)
    return "\n".join(lines)
