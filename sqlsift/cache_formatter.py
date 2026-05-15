"""Human-readable formatting for CacheReport."""
from __future__ import annotations

from sqlsift.query_cache import CacheEntry, CacheReport

_MAX_QUERY_LEN = 60


def _truncate(text: str, max_len: int = _MAX_QUERY_LEN) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def format_cache_entry(entry: CacheEntry) -> str:
    """Return a single-line summary for a cache entry."""
    ratio_pct = entry.hit_ratio * 100
    query_display = _truncate(entry.query)
    return (
        f"[hits={entry.hit_count} misses={entry.miss_count} "
        f"ratio={ratio_pct:.1f}%] {query_display}"
    )


def format_cache_report(report: CacheReport) -> str:
    """Return a formatted string summarising the full cache report."""
    lines: list[str] = []
    lines.append("=== Query Cache Report ===")
    lines.append(
        f"Total calls : {report.total_queries}"
    )
    lines.append(
        f"Cache hits  : {report.total_hits}"
    )
    lines.append(
        f"Cache misses: {report.total_misses}"
    )
    overall_pct = report.overall_hit_ratio * 100
    lines.append(f"Hit ratio   : {overall_pct:.1f}%")
    lines.append("")

    if not report.entries:
        lines.append("No queries recorded.")
        return "\n".join(lines)

    lines.append("Queries:")
    sorted_entries = sorted(
        report.entries.values(),
        key=lambda e: e.hit_ratio,
        reverse=True,
    )
    for entry in sorted_entries:
        lines.append("  " + format_cache_entry(entry))

    return "\n".join(lines)
