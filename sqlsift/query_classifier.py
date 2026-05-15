"""Classify SQL queries into operation types with metadata."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import re

from sqlsift.analyzer import AnalysisResult


_OPERATION_PATTERNS: List[tuple[str, str]] = [
    (r"^\s*SELECT", "SELECT"),
    (r"^\s*INSERT", "INSERT"),
    (r"^\s*UPDATE", "UPDATE"),
    (r"^\s*DELETE", "DELETE"),
    (r"^\s*CREATE", "CREATE"),
    (r"^\s*DROP", "DROP"),
    (r"^\s*ALTER", "ALTER"),
    (r"^\s*TRUNCATE", "TRUNCATE"),
    (r"^\s*REPLACE", "REPLACE"),
    (r"^\s*CALL", "CALL"),
]


@dataclass
class ClassifiedResult:
    result: AnalysisResult
    operation: str
    has_join: bool
    has_subquery: bool
    has_aggregate: bool
    table_count: int


@dataclass
class ClassificationReport:
    total: int
    by_operation: Dict[str, List[ClassifiedResult]] = field(default_factory=dict)

    def count_for(self, operation: str) -> int:
        return len(self.by_operation.get(operation, []))


def _detect_operation(query: str) -> str:
    upper = query.upper().strip()
    for pattern, label in _OPERATION_PATTERNS:
        if re.match(pattern, upper, re.IGNORECASE):
            return label
    return "OTHER"


def _count_tables(query: str) -> int:
    """Rough heuristic: count FROM/JOIN keywords as table references."""
    upper = query.upper()
    froms = len(re.findall(r"\bFROM\b", upper))
    joins = len(re.findall(r"\bJOIN\b", upper))
    return max(froms + joins, 1) if froms else 0


def classify_result(result: AnalysisResult) -> ClassifiedResult:
    query = result.entry.query
    upper = query.upper()
    return ClassifiedResult(
        result=result,
        operation=_detect_operation(query),
        has_join=bool(re.search(r"\bJOIN\b", upper)),
        has_subquery=bool(re.search(r"\bSELECT\b.*\bSELECT\b", upper, re.DOTALL)),
        has_aggregate=bool(re.search(r"\b(COUNT|SUM|AVG|MIN|MAX)\s*\(", upper)),
        table_count=_count_tables(query),
    )


def classify_results(results: List[AnalysisResult]) -> ClassificationReport:
    classified = [classify_result(r) for r in results]
    by_op: Dict[str, List[ClassifiedResult]] = {}
    for cr in classified:
        by_op.setdefault(cr.operation, []).append(cr)
    return ClassificationReport(total=len(classified), by_operation=by_op)
