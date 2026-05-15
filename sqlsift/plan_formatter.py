"""Formatting helpers for QueryPlan objects."""
from __future__ import annotations

from typing import List

from sqlsift.query_planner import QueryPlan

_MAX_QUERY_LEN = 72


def _truncate(text: str, max_len: int = _MAX_QUERY_LEN) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def format_plan(plan: QueryPlan, index: int | None = None) -> str:
    """Return a human-readable string for a single *plan*."""
    lines: List[str] = []
    prefix = f"[{index}] " if index is not None else ""
    lines.append(f"{prefix}Query : {_truncate(plan.query)}")

    if not plan.has_hints:
        lines.append("  (no hints)")
        return "\n".join(lines)

    for hint in plan.hints:
        lines.append(f"  • [{hint.hint}] {hint.reason}")

    return "\n".join(lines)


def format_plan_report(plans: List[QueryPlan]) -> str:
    """Return a full report string for a list of *plans*."""
    if not plans:
        return "No query plans generated."

    with_hints = [p for p in plans if p.has_hints]
    header = (
        f"Query Plan Report — {len(plans)} queries analysed, "
        f"{len(with_hints)} with hints\n"
        + "=" * 60
    )
    sections = [header]
    for i, plan in enumerate(plans, start=1):
        sections.append(format_plan(plan, index=i))

    return "\n\n".join(sections)
