"""Format cost estimates for human-readable output."""

from __future__ import annotations

from typing import List

from sqlsift.cost_estimator import CostEstimate

_MAX_QUERY_LEN = 60


def _truncate(text: str, max_len: int = _MAX_QUERY_LEN) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _bar(score: float, width: int = 20) -> str:
    """Render a simple ASCII progress bar for a 0–100 score."""
    filled = int(round(score / 100.0 * width))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def format_estimate(estimate: CostEstimate) -> str:
    lines: List[str] = [
        f"Query : {_truncate(estimate.query)}",
        f"Cost  : {estimate.cost_score:6.2f}  {_bar(estimate.cost_score)}",
        f"        duration={estimate.breakdown.get('duration', 0):.1f}  "
        f"suggestions={estimate.breakdown.get('suggestions', 0):.1f}  "
        f"severity={estimate.breakdown.get('severity', 0):.1f}",
        f"Dur ms: {estimate.duration_ms:.1f}   "
        f"Suggestions: {estimate.suggestion_count}   "
        f"Severity: {estimate.severity.value}",
    ]
    return "\n".join(lines)


def format_cost_report(estimates: List[CostEstimate]) -> str:
    if not estimates:
        return "No cost estimates available."

    header = f"{'COST REPORT':=^72}"
    parts = [header]
    for i, est in enumerate(estimates, start=1):
        parts.append(f"\n[{i}] " + format_estimate(est))
    parts.append("\n" + "=" * 72)
    parts.append(
        f"Total queries: {len(estimates)}  "
        f"Avg cost: {sum(e.cost_score for e in estimates) / len(estimates):.2f}"
    )
    return "\n".join(parts)
