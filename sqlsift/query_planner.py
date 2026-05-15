"""Query plan hint generator — suggests EXPLAIN-based hints for slow queries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from sqlsift.scorer import ScoredResult, Severity


@dataclass
class PlanHint:
    hint: str
    reason: str

    def __str__(self) -> str:
        return f"{self.hint}: {self.reason}"


@dataclass
class QueryPlan:
    query: str
    hints: List[PlanHint] = field(default_factory=list)

    @property
    def has_hints(self) -> bool:
        return len(self.hints) > 0


def _hints_for_query(query: str, severity: Severity) -> List[PlanHint]:
    hints: List[PlanHint] = []
    q = query.upper()

    if severity in (Severity.HIGH, Severity.CRITICAL):
        hints.append(PlanHint(
            hint="EXPLAIN ANALYZE",
            reason="High severity query — run EXPLAIN ANALYZE to inspect execution plan",
        ))

    if "SELECT *" in q:
        hints.append(PlanHint(
            hint="Avoid SELECT *",
            reason="Fetching all columns prevents index-only scans",
        ))

    if "WHERE" not in q and any(kw in q for kw in ("SELECT", "UPDATE", "DELETE")):
        hints.append(PlanHint(
            hint="Missing WHERE clause",
            reason="Full table scan likely — add a WHERE clause or LIMIT",
        ))

    if "LIKE '%" in q:
        hints.append(PlanHint(
            hint="Leading wildcard LIKE",
            reason="Leading wildcard prevents B-tree index usage; consider full-text search",
        ))

    if "ORDER BY" in q and "LIMIT" not in q:
        hints.append(PlanHint(
            hint="ORDER BY without LIMIT",
            reason="Sorting the full result set is expensive; add LIMIT if possible",
        ))

    if "NOT IN" in q:
        hints.append(PlanHint(
            hint="NOT IN subquery",
            reason="NOT IN with NULLs can behave unexpectedly; prefer NOT EXISTS",
        ))

    return hints


def build_query_plan(scored: ScoredResult) -> QueryPlan:
    """Return a QueryPlan with relevant hints for *scored*."""
    query = scored.result.entry.query
    hints = _hints_for_query(query, scored.severity)
    return QueryPlan(query=query, hints=hints)


def build_query_plans(scored_results: List[ScoredResult]) -> List[QueryPlan]:
    """Build query plans for every result in *scored_results*."""
    return [build_query_plan(s) for s in scored_results]
