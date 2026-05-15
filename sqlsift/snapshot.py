"""Snapshot module: capture and compare pipeline result snapshots over time."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlsift.analyzer import AnalysisResult
from sqlsift.exporter import result_to_dict


@dataclass
class Snapshot:
    """A timestamped collection of analysis results."""
    timestamp: str
    label: str
    results: List[Dict]

    @property
    def query_count(self) -> int:
        return len(self.results)

    @property
    def slow_count(self) -> int:
        return sum(1 for r in self.results if r.get("is_slow", False))


def create_snapshot(
    results: List[AnalysisResult],
    label: str = "",
    timestamp: Optional[str] = None,
) -> Snapshot:
    """Build a Snapshot from a list of AnalysisResult objects."""
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    return Snapshot(
        timestamp=ts,
        label=label,
        results=[result_to_dict(r) for r in results],
    )


def save_snapshot(snapshot: Snapshot, path: str) -> None:
    """Persist a snapshot to a JSON file."""
    data = {
        "timestamp": snapshot.timestamp,
        "label": snapshot.label,
        "results": snapshot.results,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def load_snapshot(path: str) -> Snapshot:
    """Load a snapshot from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return Snapshot(
        timestamp=data["timestamp"],
        label=data.get("label", ""),
        results=data["results"],
    )


def diff_snapshots(before: Snapshot, after: Snapshot) -> Dict:
    """Return a simple diff summary between two snapshots."""
    before_queries = {r["query"] for r in before.results}
    after_queries = {r["query"] for r in after.results}

    added = after_queries - before_queries
    removed = before_queries - after_queries

    before_slow = {r["query"] for r in before.results if r.get("is_slow", False)}
    after_slow = {r["query"] for r in after.results if r.get("is_slow", False)}
    newly_slow = (after_slow - before_slow) - removed

    return {
        "added_queries": sorted(added),
        "removed_queries": sorted(removed),
        "newly_slow_queries": sorted(newly_slow),
        "slow_count_before": before.slow_count,
        "slow_count_after": after.slow_count,
    }
