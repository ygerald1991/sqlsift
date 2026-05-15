"""Detect common anti-patterns in SQL queries and produce structured findings."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from sqlsift.analyzer import AnalysisResult


@dataclass
class PatternFinding:
    pattern_id: str
    description: str
    severity: str  # "low" | "medium" | "high"
    query: str


@dataclass
class PatternReport:
    findings: List[PatternFinding] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.findings)

    def by_severity(self, severity: str) -> List[PatternFinding]:
        return [f for f in self.findings if f.severity == severity]


_PATTERNS: List[tuple[str, str, str, str]] = [
    (
        "select_star",
        r"SELECT\s+\*",
        "medium",
        "SELECT * retrieves all columns; prefer explicit column list",
    ),
    (
        "leading_wildcard",
        r"LIKE\s+['\"]%",
        "high",
        "Leading wildcard in LIKE prevents index usage",
    ),
    (
        "or_in_where",
        r"WHERE\b.*\bOR\b",
        "medium",
        "OR in WHERE clause may hinder index selection",
    ),
    (
        "not_in",
        r"\bNOT\s+IN\b",
        "medium",
        "NOT IN can be slow on large sets; consider NOT EXISTS",
    ),
    (
        "missing_limit",
        r"SELECT\b(?!.*\bLIMIT\b)",
        "low",
        "Query lacks LIMIT clause; may return unbounded rows",
    ),
    (
        "order_without_limit",
        r"ORDER\s+BY\b(?!.*\bLIMIT\b)",
        "low",
        "ORDER BY without LIMIT may cause full sort on large tables",
    ),
]


def detect_patterns(result: AnalysisResult) -> List[PatternFinding]:
    """Return all anti-pattern findings for a single AnalysisResult."""
    query_upper = result.entry.query.upper()
    findings: List[PatternFinding] = []
    for pid, regex, severity, description in _PATTERNS:
        if re.search(regex, query_upper):
            findings.append(
                PatternFinding(
                    pattern_id=pid,
                    description=description,
                    severity=severity,
                    query=result.entry.query,
                )
            )
    return findings


def build_pattern_report(results: List[AnalysisResult]) -> PatternReport:
    """Aggregate pattern findings across all results."""
    all_findings: List[PatternFinding] = []
    for result in results:
        all_findings.extend(detect_patterns(result))
    return PatternReport(findings=all_findings)
