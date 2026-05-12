"""Reporter module for formatting and outputting analysis results."""

from dataclasses import dataclass
from typing import List, Optional
from sqlsift.analyzer import AnalysisResult


@dataclass
class Report:
    """A formatted report summarizing analysis results."""
    total_queries: int
    slow_queries: int
    entries_with_suggestions: int
    suggestions_by_query: List[dict]

    @property
    def slow_query_ratio(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return self.slow_queries / self.total_queries


def build_report(results: List[AnalysisResult]) -> Report:
    """Build a Report from a list of AnalysisResult objects."""
    total = len(results)
    slow = sum(1 for r in results if r.is_slow)
    with_suggestions = sum(1 for r in results if r.suggestions)

    suggestions_by_query = [
        {
            "query": r.entry.query,
            "duration_ms": r.entry.duration_ms,
            "suggestions": r.suggestions,
        }
        for r in results
        if r.suggestions
    ]

    return Report(
        total_queries=total,
        slow_queries=slow,
        entries_with_suggestions=with_suggestions,
        suggestions_by_query=suggestions_by_query,
    )


def format_report(report: Report, verbose: bool = False) -> str:
    """Format a Report as a human-readable string."""
    lines = [
        "=== SQLSift Report ===",
        f"Total queries analyzed : {report.total_queries}",
        f"Slow queries detected  : {report.slow_queries} "
        f"({report.slow_query_ratio:.1%})",
        f"Queries with suggestions: {report.entries_with_suggestions}",
    ]

    if verbose and report.suggestions_by_query:
        lines.append("\n--- Suggestions ---")
        for item in report.suggestions_by_query:
            lines.append(f"\nQuery : {item['query'][:80]}")
            lines.append(f"Duration: {item['duration_ms']} ms")
            for suggestion in item["suggestions"]:
                lines.append(f"  • {suggestion}")

    return "\n".join(lines)
