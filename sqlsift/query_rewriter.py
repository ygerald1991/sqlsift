"""Suggest rewritten versions of slow queries for better performance."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from sqlsift.scorer import ScoredResult, Severity


@dataclass
class RewriteSuggestion:
    original: str
    rewritten: str
    reason: str

    def __str__(self) -> str:
        return f"[{self.reason}] {self.rewritten}"


@dataclass
class RewriteResult:
    query: str
    suggestions: List[RewriteSuggestion] = field(default_factory=list)

    @property
    def has_suggestions(self) -> bool:
        return len(self.suggestions) > 0


def _rewrite_select_star(query: str) -> RewriteSuggestion | None:
    import re
    if re.search(r"SELECT\s+\*", query, re.IGNORECASE):
        rewritten = re.sub(r"SELECT\s+\*", "SELECT <explicit_columns>", query, flags=re.IGNORECASE)
        return RewriteSuggestion(
            original=query,
            rewritten=rewritten,
            reason="Replace SELECT * with explicit column list",
        )
    return None


def _rewrite_or_to_union(query: str) -> RewriteSuggestion | None:
    import re
    if re.search(r"WHERE\s+.+\s+OR\s+", query, re.IGNORECASE):
        return RewriteSuggestion(
            original=query,
            rewritten=query + "  -- consider rewriting OR conditions as UNION ALL",
            reason="Replace OR in WHERE with UNION ALL for index utilisation",
        )
    return None


def _rewrite_not_in(query: str) -> RewriteSuggestion | None:
    import re
    if re.search(r"NOT\s+IN\s*\(", query, re.IGNORECASE):
        return RewriteSuggestion(
            original=query,
            rewritten=query + "  -- consider NOT EXISTS or LEFT JOIN ... WHERE col IS NULL",
            reason="Replace NOT IN with NOT EXISTS or anti-join",
        )
    return None


_REWRITERS = [_rewrite_select_star, _rewrite_or_to_union, _rewrite_not_in]


def rewrite_query(scored: ScoredResult) -> RewriteResult:
    """Generate rewrite suggestions for a single scored result."""
    if scored.severity not in (Severity.HIGH, Severity.CRITICAL):
        return RewriteResult(query=scored.result.entry.query)

    query = scored.result.entry.query
    suggestions: List[RewriteSuggestion] = []
    for rewriter in _REWRITERS:
        suggestion = rewriter(query)
        if suggestion is not None:
            suggestions.append(suggestion)

    return RewriteResult(query=query, suggestions=suggestions)


def rewrite_queries(scored_results: List[ScoredResult]) -> List[RewriteResult]:
    """Generate rewrite suggestions for a list of scored results."""
    return [rewrite_query(r) for r in scored_results]
