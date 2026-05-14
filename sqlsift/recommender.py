"""Generates prioritized optimization recommendations from scored results."""

from dataclasses import dataclass, field
from typing import List, Dict
from sqlsift.scorer import ScoredResult, Severity


@dataclass
class Recommendation:
    query: str
    severity: Severity
    score: float
    suggestions: List[str]
    priority: int  # 1 = highest


@dataclass
class RecommendationReport:
    recommendations: List[Recommendation] = field(default_factory=list)
    total: int = 0
    critical_count: int = 0
    high_count: int = 0


def _priority_from_severity(severity: Severity) -> int:
    order = {
        Severity.CRITICAL: 1,
        Severity.HIGH: 2,
        Severity.MEDIUM: 3,
        Severity.LOW: 4,
    }
    return order.get(severity, 99)


def build_recommendations(scored: List[ScoredResult]) -> RecommendationReport:
    """Convert scored results into a prioritized recommendation report."""
    recs: List[Recommendation] = []

    for sr in scored:
        if not sr.result.suggestions:
            continue
        priority = _priority_from_severity(sr.severity)
        recs.append(
            Recommendation(
                query=sr.result.entry.query,
                severity=sr.severity,
                score=sr.score,
                suggestions=list(sr.result.suggestions),
                priority=priority,
            )
        )

    recs.sort(key=lambda r: (r.priority, -r.score))

    critical = sum(1 for r in recs if r.severity == Severity.CRITICAL)
    high = sum(1 for r in recs if r.severity == Severity.HIGH)

    return RecommendationReport(
        recommendations=recs,
        total=len(recs),
        critical_count=critical,
        high_count=high,
    )


def format_recommendations(report: RecommendationReport, max_results: int = 10) -> str:
    """Format a recommendation report as a human-readable string."""
    lines: List[str] = [
        f"Recommendation Report — {report.total} queries with suggestions",
        f"  Critical: {report.critical_count}  High: {report.high_count}",
        "-" * 60,
    ]
    for i, rec in enumerate(report.recommendations[:max_results], start=1):
        query_preview = rec.query[:60] + "..." if len(rec.query) > 60 else rec.query
        lines.append(f"[{i}] [{rec.severity.value.upper()}] score={rec.score:.1f}")
        lines.append(f"    Query : {query_preview}")
        for suggestion in rec.suggestions:
            lines.append(f"    • {suggestion}")
    if not report.recommendations:
        lines.append("  No actionable recommendations found.")
    return "\n".join(lines)
