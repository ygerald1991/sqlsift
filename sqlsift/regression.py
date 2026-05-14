"""Regression detection: compare current results against a saved baseline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlsift.analyzer import AnalysisResult
from sqlsift.baseline import Baseline, BaselineEntry


@dataclass
class RegressionItem:
    query: str
    baseline_duration: Optional[float]
    current_duration: float
    duration_delta: float
    baseline_suggestions: Optional[int]
    current_suggestions: int
    is_new: bool


@dataclass
class RegressionReport:
    regressions: List[RegressionItem] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.regressions)

    @property
    def new_queries(self) -> List[RegressionItem]:
        return [r for r in self.regressions if r.is_new]

    @property
    def worsened_queries(self) -> List[RegressionItem]:
        return [r for r in self.regressions if not r.is_new]


_DURATION_THRESHOLD = 0.10  # 10% increase triggers regression
_SUGGESTION_INCREASE = 1    # any new suggestion triggers regression


def detect_regressions(
    results: List[AnalysisResult],
    baseline: Baseline,
    duration_threshold: float = _DURATION_THRESHOLD,
) -> RegressionReport:
    """Return a RegressionReport for results that regressed vs the baseline."""
    items: List[RegressionItem] = []

    for result in results:
        if not result.is_slow:
            continue
        q = result.entry.query
        entry: Optional[BaselineEntry] = baseline.get(q)
        current_dur = result.entry.duration
        current_sug = len(result.suggestions)

        if entry is None:
            items.append(
                RegressionItem(
                    query=q,
                    baseline_duration=None,
                    current_duration=current_dur,
                    duration_delta=current_dur,
                    baseline_suggestions=None,
                    current_suggestions=current_sug,
                    is_new=True,
                )
            )
            continue

        delta = current_dur - entry.avg_duration
        relative = delta / entry.avg_duration if entry.avg_duration > 0 else 0.0
        sug_increase = current_sug - entry.suggestion_count

        if relative > duration_threshold or sug_increase >= _SUGGESTION_INCREASE:
            items.append(
                RegressionItem(
                    query=q,
                    baseline_duration=entry.avg_duration,
                    current_duration=current_dur,
                    duration_delta=delta,
                    baseline_suggestions=entry.suggestion_count,
                    current_suggestions=current_sug,
                    is_new=False,
                )
            )

    return RegressionReport(regressions=items)
