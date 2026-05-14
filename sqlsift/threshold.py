"""Threshold configuration for slow query detection."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class ThresholdConfig:
    """Holds per-table and global slow query thresholds (in seconds)."""

    global_threshold: float = 1.0
    per_table: Dict[str, float] = field(default_factory=dict)

    def get_threshold(self, table: Optional[str] = None) -> float:
        """Return the effective threshold for the given table name."""
        if table and table in self.per_table:
            return self.per_table[table]
        return self.global_threshold

    def is_slow(self, duration: float, table: Optional[str] = None) -> bool:
        """Return True if *duration* exceeds the effective threshold."""
        return duration >= self.get_threshold(table)


def load_threshold_config(path: str | Path) -> ThresholdConfig:
    """Load a ThresholdConfig from a JSON file.

    Expected JSON shape::

        {
            "global_threshold": 1.0,
            "per_table": {
                "orders": 0.5,
                "events": 2.0
            }
        }
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ThresholdConfig(
        global_threshold=float(data.get("global_threshold", 1.0)),
        per_table={k: float(v) for k, v in data.get("per_table", {}).items()},
    )


def default_config() -> ThresholdConfig:
    """Return a ThresholdConfig with library defaults."""
    return ThresholdConfig()
