"""Index advisor: suggests missing indexes based on query patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Dict

from sqlsift.analyzer import AnalysisResult
from sqlsift.scorer import ScoredResult, Severity


@dataclass
class IndexSuggestion:
    table: str
    columns: List[str]
    reason: str

    def __str__(self) -> str:
        cols = ", ".join(self.columns)
        return f"CREATE INDEX ON {self.table} ({cols});  -- {self.reason}"


@dataclass
class IndexAdvice:
    query: str
    suggestions: List[IndexSuggestion] = field(default_factory=list)

    @property
    def has_suggestions(self) -> bool:
        return bool(self.suggestions)


_WHERE_COL_RE = re.compile(
    r"WHERE\s+(?:[`\"]?(?P<tbl>\w+)[`\"]?\.)?[`\"]?(?P<col>\w+)[`\"]?\s*[=<>!]",
    re.IGNORECASE,
)
_FROM_RE = re.compile(r"FROM\s+[`\"]?(?P<tbl>\w+)[`\"]?", re.IGNORECASE)
_ORDER_RE = re.compile(
    r"ORDER\s+BY\s+(?:[`\"]?\w+[`\"]?\.)?[`\"]?(?P<col>\w+)[`\"]?",
    re.IGNORECASE,
)


def _primary_table(query: str) -> str:
    m = _FROM_RE.search(query)
    return m.group("tbl") if m else "unknown"


def advise_indexes(scored: ScoredResult) -> IndexAdvice:
    """Produce index suggestions for a single scored result."""
    query = scored.result.entry.query
    advice = IndexAdvice(query=query)

    if scored.severity not in (Severity.HIGH, Severity.CRITICAL):
        return advice

    table = _primary_table(query)

    where_match = _WHERE_COL_RE.search(query)
    if where_match:
        col = where_match.group("col")
        tbl = where_match.group("tbl") or table
        advice.suggestions.append(
            IndexSuggestion(
                table=tbl,
                columns=[col],
                reason=f"column used in WHERE filter",
            )
        )

    order_match = _ORDER_RE.search(query)
    if order_match:
        col = order_match.group("col")
        advice.suggestions.append(
            IndexSuggestion(
                table=table,
                columns=[col],
                reason="column used in ORDER BY",
            )
        )

    return advice


def advise_all(scored_results: List[ScoredResult]) -> Dict[str, IndexAdvice]:
    """Return a mapping of query -> IndexAdvice for all scored results."""
    out: Dict[str, IndexAdvice] = {}
    for sr in scored_results:
        advice = advise_indexes(sr)
        if advice.has_suggestions:
            out[sr.result.entry.query] = advice
    return out
