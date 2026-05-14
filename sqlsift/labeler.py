"""Assigns human-readable labels to queries based on their SQL pattern."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from sqlsift.analyzer import AnalysisResult


# Ordered list of (pattern, label) pairs; first match wins.
_LABEL_RULES: List[tuple[str, str]] = [
    (r"(?i)^\s*SELECT\b.*\bJOIN\b", "join-query"),
    (r"(?i)^\s*SELECT\b.*\bGROUP\s+BY\b", "aggregation"),
    (r"(?i)^\s*SELECT\b.*\bORDER\s+BY\b", "sorted-read"),
    (r"(?i)^\s*SELECT\b.*\bLIKE\b", "pattern-match"),
    (r"(?i)^\s*SELECT\b.*\bIN\s*\(", "in-clause"),
    (r"(?i)^\s*SELECT\b", "simple-read"),
    (r"(?i)^\s*INSERT\b", "write-insert"),
    (r"(?i)^\s*UPDATE\b", "write-update"),
    (r"(?i)^\s*DELETE\b", "write-delete"),
    (r"(?i)^\s*CREATE\b", "ddl"),
    (r"(?i)^\s*DROP\b", "ddl"),
    (r"(?i)^\s*ALTER\b", "ddl"),
]

_COMPILED_RULES: List[tuple[re.Pattern[str], str]] = [
    (re.compile(pattern), label) for pattern, label in _LABEL_RULES
]


@dataclass
class LabeledResult:
    result: AnalysisResult
    label: str
    extra_labels: List[str] = field(default_factory=list)

    @property
    def all_labels(self) -> List[str]:
        return [self.label] + self.extra_labels


def _primary_label(query: str) -> str:
    """Return the first matching label for *query*, or 'unknown'."""
    for pattern, label in _COMPILED_RULES:
        if pattern.search(query):
            return label
    return "unknown"


def _extra_labels(query: str) -> List[str]:
    """Return additional descriptive labels beyond the primary one."""
    extras: List[str] = []
    if re.search(r"(?i)\bSUBQUERY\b|\bSELECT\b.*\(\s*SELECT\b", query):
        extras.append("subquery")
    if re.search(r"(?i)\bLIMIT\b", query):
        extras.append("limited")
    if re.search(r"(?i)\bDISTINCT\b", query):
        extras.append("distinct")
    return extras


def label_result(result: AnalysisResult) -> LabeledResult:
    """Attach a primary label and optional extra labels to *result*."""
    query = result.entry.query
    return LabeledResult(
        result=result,
        label=_primary_label(query),
        extra_labels=_extra_labels(query),
    )


def label_results(results: List[AnalysisResult]) -> List[LabeledResult]:
    """Label every result in *results*."""
    return [label_result(r) for r in results]
