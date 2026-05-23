"""Generates stable fingerprints for SQL queries for grouping and tracking."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Dict, List

from sqlsift.analyzer import AnalysisResult


@dataclass
class Fingerprint:
    raw: str
    normalized: str
    digest: str  # short hex digest

    def __str__(self) -> str:
        return self.digest


@dataclass
class FingerprintGroup:
    fingerprint: Fingerprint
    results: List[AnalysisResult] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.results)

    @property
    def avg_duration(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.entry.duration_ms for r in self.results) / len(self.results)

    @property
    def max_duration(self) -> float:
        if not self.results:
            return 0.0
        return max(r.entry.duration_ms for r in self.results)


def _normalize(query: str) -> str:
    """Strip comments, collapse whitespace, and replace literals."""
    # Remove single-line comments
    query = re.sub(r"--[^\n]*", " ", query)
    # Remove block comments
    query = re.sub(r"/\*.*?\*/", " ", query, flags=re.DOTALL)
    # Replace string literals
    query = re.sub(r"'[^']*'", "?", query)
    # Replace numeric literals
    query = re.sub(r"\b\d+(\.\d+)?\b", "?", query)
    # Collapse whitespace
    query = re.sub(r"\s+", " ", query).strip().upper()
    return query


def _digest(normalized: str) -> str:
    return hashlib.sha1(normalized.encode()).hexdigest()[:12]


def fingerprint_query(query: str) -> Fingerprint:
    """Compute a Fingerprint for a single SQL query string."""
    normalized = _normalize(query)
    return Fingerprint(raw=query, normalized=normalized, digest=_digest(normalized))


def group_by_fingerprint(
    results: List[AnalysisResult],
) -> Dict[str, FingerprintGroup]:
    """Group AnalysisResults by their query fingerprint digest."""
    groups: Dict[str, FingerprintGroup] = {}
    for result in results:
        fp = fingerprint_query(result.entry.query)
        if fp.digest not in groups:
            groups[fp.digest] = FingerprintGroup(fingerprint=fp)
        groups[fp.digest].results.append(result)
    return groups
