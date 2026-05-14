"""Summarizer: produce a high-level text summary of a pipeline run."""

from dataclasses import dataclass
from typing import List

from sqlsift.analyzer import AnalysisResult
from sqlsift.reporter import Report, slow_query_ratio
from sqlsift.scorer import ScoredResult, Severity


@dataclass
class RunSummary:
    total_queries: int
    slow_queries: int
    slow_ratio: float
    avg_duration_ms: float
    max_duration_ms: float
    critical_count: int
    warning_count: int
    info_count: int
    top_suggestions: List[str]


def _top_suggestions(results: List[AnalysisResult], n: int = 3) -> List[str]:
    """Return the n most frequently occurring suggestions across all results."""
    freq: dict = {}
    for r in results:
        for s in r.suggestions:
            freq[s] = freq.get(s, 0) + 1
    sorted_suggestions = sorted(freq, key=lambda k: freq[k], reverse=True)
    return sorted_suggestions[:n]


def build_summary(report: Report, scored: List[ScoredResult]) -> RunSummary:
    """Build a RunSummary from a Report and a list of ScoredResults."""
    durations = [r.result.entry.duration_ms for r in scored]
    avg_dur = sum(durations) / len(durations) if durations else 0.0
    max_dur = max(durations) if durations else 0.0

    critical = sum(1 for r in scored if r.severity == Severity.CRITICAL)
    warning = sum(1 for r in scored if r.severity == Severity.WARNING)
    info = sum(1 for r in scored if r.severity == Severity.INFO)

    suggestions = _top_suggestions([r.result for r in scored])

    return RunSummary(
        total_queries=report.total,
        slow_queries=report.slow_count,
        slow_ratio=slow_query_ratio(report),
        avg_duration_ms=round(avg_dur, 2),
        max_duration_ms=round(max_dur, 2),
        critical_count=critical,
        warning_count=warning,
        info_count=info,
        top_suggestions=suggestions,
    )


def format_summary(summary: RunSummary) -> str:
    """Render a RunSummary as a human-readable string."""
    lines = [
        "=== SQLSift Run Summary ===",
        f"Total queries   : {summary.total_queries}",
        f"Slow queries    : {summary.slow_queries} ({summary.slow_ratio:.1%})",
        f"Avg duration    : {summary.avg_duration_ms} ms",
        f"Max duration    : {summary.max_duration_ms} ms",
        f"Severity counts : CRITICAL={summary.critical_count}  "
        f"WARNING={summary.warning_count}  INFO={summary.info_count}",
    ]
    if summary.top_suggestions:
        lines.append("Top suggestions :")
        for i, s in enumerate(summary.top_suggestions, 1):
            lines.append(f"  {i}. {s}")
    else:
        lines.append("Top suggestions : none")
    return "\n".join(lines)
