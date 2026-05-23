"""Format normalized query results for display."""
from __future__ import annotations

from typing import List

from sqlsift.query_normalizer import NormalizedQuery

_MAX_LEN = 80
_INDENT = "  "
_SEPARATOR = "=" * 60


def _truncate(text: str, max_len: int = _MAX_LEN) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def format_normalized(entry: NormalizedQuery, max_len: int = _MAX_LEN) -> str:
    """Return a human-readable string for a single NormalizedQuery."""
    original = _truncate(entry.original.replace("\n", " "), max_len)
    normalized = _truncate(entry.normalized, max_len)
    fingerprint = entry.fingerprint or "(empty)"
    lines = [
        f"Original   : {original}",
        f"Normalized : {normalized}",
        f"Fingerprint: {fingerprint}",
    ]
    return "\n".join(lines)


def format_normalized_report(
    entries: List[NormalizedQuery],
    max_len: int = _MAX_LEN,
) -> str:
    """Return a formatted report for a list of NormalizedQuery objects."""
    if not entries:
        return "No normalized queries."

    total = len(entries)
    unique_fps = len({e.fingerprint for e in entries if e.fingerprint})

    header = [
        _SEPARATOR,
        f"Normalized Query Report",
        f"Total queries : {total}",
        f"Unique patterns: {unique_fps}",
        _SEPARATOR,
    ]

    blocks: List[str] = []
    for i, entry in enumerate(entries, start=1):
        block = f"[{i}]\n" + "\n".join(
            f"{_INDENT}{line}" for line in format_normalized(entry, max_len).splitlines()
        )
        blocks.append(block)

    return "\n".join(header) + "\n" + "\n\n".join(blocks)


def format_fingerprint_groups(
    entries: List[NormalizedQuery],
    max_len: int = _MAX_LEN,
) -> str:
    """Return a report grouping queries by their fingerprint.

    Queries with the same fingerprint share the same structural pattern.
    Each group shows the fingerprint and the count of matching queries,
    followed by the original query text for each occurrence.
    """
    if not entries:
        return "No normalized queries."

    groups: dict[str, List[NormalizedQuery]] = {}
    for entry in entries:
        key = entry.fingerprint or "(empty)"
        groups.setdefault(key, []).append(entry)

    lines = [_SEPARATOR, "Fingerprint Groups", _SEPARATOR]
    for fp, group in sorted(groups.items(), key=lambda x: -len(x[1])):
        lines.append(f"Fingerprint: {fp}  (count: {len(group)})")
        for entry in group:
            truncated = _truncate(entry.original.replace("\n", " "), max_len)
            lines.append(f"{_INDENT}- {truncated}")
        lines.append("")

    return "\n".join(lines).rstrip()
