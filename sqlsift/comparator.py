"""Compare two sets of analysis results to surface regressions or improvements."""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from sqlsift.analyzer import AnalysisResult


@dataclass
class ComparisonSummary:
    """Summary of differences between a baseline and a current result set."""

    new_slow_queries: List[AnalysisResult] = field(default_factory=list)
    resolved_slow_queries: List[AnalysisResult] = field(default_factory=list)
    regressed: List[Tuple[AnalysisResult, AnalysisResult]] = field(default_factory=list)  # (baseline, current)
    improved: List[Tuple[AnalysisResult, AnalysisResult]] = field(default_factory=list)   # (baseline, current)
    unchanged: List[AnalysisResult] = field(default_factory=list)


def _index_by_query(results: List[AnalysisResult]) -> Dict[str, AnalysisResult]:
    """Build a mapping of query text -> AnalysisResult for fast lookup."""
    return {r.entry.query: r for r in results}


def compare_results(
    baseline: List[AnalysisResult],
    current: List[AnalysisResult],
    duration_threshold: float = 0.1,
) -> ComparisonSummary:
    """Compare *current* results against a *baseline* set.

    A query is considered *regressed* when its duration increased by more than
    *duration_threshold* seconds relative to the baseline.  Conversely, it is
    *improved* when the duration decreased by more than the threshold.

    Args:
        baseline: Results from an earlier run (the reference point).
        current:  Results from the most-recent run.
        duration_threshold: Minimum absolute duration change (seconds) that
            qualifies as a regression or improvement.

    Returns:
        A :class:`ComparisonSummary` describing the differences.
    """
    baseline_index = _index_by_query(baseline)
    current_index = _index_by_query(current)

    summary = ComparisonSummary()

    for query, cur in current_index.items():
        if query not in baseline_index:
            if cur.is_slow:
                summary.new_slow_queries.append(cur)
            continue

        base = baseline_index[query]
        delta = cur.entry.duration - base.entry.duration

        if delta > duration_threshold:
            summary.regressed.append((base, cur))
        elif delta < -duration_threshold:
            summary.improved.append((base, cur))
        else:
            summary.unchanged.append(cur)

    for query, base in baseline_index.items():
        if query not in current_index and base.is_slow:
            summary.resolved_slow_queries.append(base)

    return summary
