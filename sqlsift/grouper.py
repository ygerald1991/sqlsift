"""Group analysis results by a chosen dimension (table, operation, hour)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from sqlsift.analyzer import AnalysisResult


class GroupBy(str, Enum):
    TABLE = "table"
    OPERATION = "operation"
    HOUR = "hour"


@dataclass
class ResultGroup:
    key: str
    results: List[AnalysisResult] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.results)

    @property
    def avg_duration(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.entry.duration for r in self.results) / len(self.results)

    @property
    def slow_count(self) -> int:
        return sum(1 for r in self.results if r.is_slow)

    @property
    def slow_ratio(self) -> float:
        if not self.results:
            return 0.0
        return self.slow_count / len(self.results)


def _key_for(result: AnalysisResult, by: GroupBy) -> str:
    query = result.entry.query.strip().upper()
    if by == GroupBy.OPERATION:
        first_token = query.split()[0] if query.split() else "UNKNOWN"
        return first_token
    if by == GroupBy.TABLE:
        tokens = query.split()
        for i, token in enumerate(tokens):
            if token in ("FROM", "INTO", "UPDATE", "JOIN") and i + 1 < len(tokens):
                return tokens[i + 1].strip(",;()")
        return "UNKNOWN"
    if by == GroupBy.HOUR:
        ts = result.entry.timestamp
        if ts:
            return ts[:13]  # "YYYY-MM-DD HH"
        return "UNKNOWN"
    return "UNKNOWN"


def group_results(
    results: List[AnalysisResult],
    by: GroupBy = GroupBy.OPERATION,
) -> Dict[str, ResultGroup]:
    """Partition *results* into named groups according to *by*."""
    groups: Dict[str, ResultGroup] = {}
    for result in results:
        key = _key_for(result, by)
        if key not in groups:
            groups[key] = ResultGroup(key=key)
        groups[key].results.append(result)
    return groups
