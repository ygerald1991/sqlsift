"""Format query rewrite suggestions for human-readable output."""
from __future__ import annotations

from typing import List

from sqlsift.query_rewriter import RewriteResult

_MAX_LEN = 120


def _truncate(text: str, max_len: int = _MAX_LEN) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def format_rewrite_result(result: RewriteResult, index: int | None = None) -> str:
    lines: List[str] = []
    prefix = f"[{index}] " if index is not None else ""
    lines.append(f"{prefix}Query : {_truncate(result.query)}")

    if not result.has_suggestions:
        lines.append("  No rewrite suggestions.")
        return "\n".join(lines)

    lines.append(f"  Rewrite suggestions ({len(result.suggestions)}):")
    for i, suggestion in enumerate(result.suggestions, start=1):
        lines.append(f"  {i}. Reason  : {suggestion.reason}")
        lines.append(f"     Rewrite : {_truncate(suggestion.rewritten)}")

    return "\n".join(lines)


def format_rewrite_report(results: List[RewriteResult]) -> str:
    if not results:
        return "No rewrite results to display."

    actionable = [r for r in results if r.has_suggestions]
    header = (
        f"Query Rewrite Report\n"
        f"{'=' * 40}\n"
        f"Total queries analysed : {len(results)}\n"
        f"Queries with rewrites  : {len(actionable)}\n"
        f"{'=' * 40}"
    )

    sections = [header]
    for idx, result in enumerate(results, start=1):
        if result.has_suggestions:
            sections.append(format_rewrite_result(result, index=idx))

    if not actionable:
        sections.append("All queries look fine — no rewrites suggested.")

    return "\n\n".join(sections)
