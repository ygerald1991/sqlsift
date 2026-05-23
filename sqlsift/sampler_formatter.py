"""sampler_formatter.py — human-readable formatting for SampleReport."""
from __future__ import annotations

from sqlsift.query_sampler import SampleReport

_MAX_QUERY_LEN = 72


def _truncate(text: str, max_len: int = _MAX_QUERY_LEN) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def format_sample_report(report: SampleReport) -> str:
    """Return a multi-line summary of a SampleReport."""
    lines: list[str] = [
        "=== Query Sample Report ===",
        f"Sampled : {report.count} / {report.total_seen} queries",
        f"Coverage: {report.coverage_ratio:.1%}",
        "",
    ]

    if not report.results:
        lines.append("  (no results in sample)")
        return "\n".join(lines)

    for i, result in enumerate(report.results, start=1):
        query_display = _truncate(result.entry.query)
        slow_tag = "[SLOW]" if result.is_slow else "[ok]  "
        lines.append(
            f"  {i:>4}. {slow_tag} {result.entry.duration_ms:>8.1f} ms  {query_display}"
        )

    return "\n".join(lines)
