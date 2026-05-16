"""Track query execution frequency and timing across analysis runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlsift.analyzer import AnalysisResult
from sqlsift.aggregator import normalize_pattern


@dataclass
class ExecutionRecord:
    query_pattern: str
    call_count: int = 0
    total_duration: float = 0.0
    durations: List[float] = field(default_factory=list)

    @property
    def avg_duration(self) -> float:
        return self.total_duration / self.call_count if self.call_count else 0.0

    @property
    def max_duration(self) -> float:
        return max(self.durations) if self.durations else 0.0

    @property
    def min_duration(self) -> float:
        return min(self.durations) if self.durations else 0.0


@dataclass
class ExecutionReport:
    records: Dict[str, ExecutionRecord] = field(default_factory=dict)

    @property
    def total_queries(self) -> int:
        return sum(r.call_count for r in self.records.values())

    @property
    def unique_patterns(self) -> int:
        return len(self.records)

    def most_frequent(self, n: int = 5) -> List[ExecutionRecord]:
        sorted_records = sorted(
            self.records.values(), key=lambda r: r.call_count, reverse=True
        )
        return sorted_records[:n]

    def slowest_avg(self, n: int = 5) -> List[ExecutionRecord]:
        sorted_records = sorted(
            self.records.values(), key=lambda r: r.avg_duration, reverse=True
        )
        return sorted_records[:n]


def track_executions(results: List[AnalysisResult]) -> ExecutionReport:
    """Build an ExecutionReport from a list of AnalysisResult objects."""
    report = ExecutionReport()
    for result in results:
        query = result.entry.query if result.entry.query else ""
        pattern = normalize_pattern(query)
        if pattern not in report.records:
            report.records[pattern] = ExecutionRecord(query_pattern=pattern)
        record = report.records[pattern]
        record.call_count += 1
        duration = result.entry.duration or 0.0
        record.total_duration += duration
        record.durations.append(duration)
    return report
