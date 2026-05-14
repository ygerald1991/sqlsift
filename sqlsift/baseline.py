"""Baseline management: save and load reference snapshots of analysis results."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from sqlsift.analyzer import AnalysisResult


@dataclass
class BaselineEntry:
    query: str
    avg_duration: float
    suggestion_count: int
    occurrences: int


@dataclass
class Baseline:
    entries: Dict[str, BaselineEntry] = field(default_factory=dict)

    def get(self, query: str) -> Optional[BaselineEntry]:
        return self.entries.get(query)


def _result_to_entry(result: AnalysisResult) -> BaselineEntry:
    return BaselineEntry(
        query=result.entry.query,
        avg_duration=result.entry.duration,
        suggestion_count=len(result.suggestions),
        occurrences=1,
    )


def build_baseline(results: List[AnalysisResult]) -> Baseline:
    """Build a baseline snapshot from a list of analysis results."""
    entries: Dict[str, BaselineEntry] = {}
    for result in results:
        q = result.entry.query
        if q not in entries:
            entries[q] = BaselineEntry(
                query=q,
                avg_duration=result.entry.duration,
                suggestion_count=len(result.suggestions),
                occurrences=1,
            )
        else:
            existing = entries[q]
            total = existing.avg_duration * existing.occurrences + result.entry.duration
            existing.occurrences += 1
            existing.avg_duration = total / existing.occurrences
            existing.suggestion_count = max(existing.suggestion_count, len(result.suggestions))
    return Baseline(entries=entries)


def save_baseline(baseline: Baseline, path: str) -> None:
    """Persist a baseline to a JSON file."""
    data = [
        {
            "query": e.query,
            "avg_duration": e.avg_duration,
            "suggestion_count": e.suggestion_count,
            "occurrences": e.occurrences,
        }
        for e in baseline.entries.values()
    ]
    Path(path).write_text(json.dumps(data, indent=2))


def load_baseline(path: str) -> Baseline:
    """Load a baseline from a JSON file."""
    raw = json.loads(Path(path).read_text())
    entries = {
        item["query"]: BaselineEntry(
            query=item["query"],
            avg_duration=item["avg_duration"],
            suggestion_count=item["suggestion_count"],
            occurrences=item["occurrences"],
        )
        for item in raw
    }
    return Baseline(entries=entries)
