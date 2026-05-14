"""Watchlist: flag results whose query matches user-defined patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from sqlsift.analyzer import AnalysisResult


@dataclass
class WatchlistEntry:
    """A single pattern to watch for, with an optional label."""

    pattern: str
    label: str = ""
    _compiled: Optional[re.Pattern] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._compiled = re.compile(self.pattern, re.IGNORECASE)

    def matches(self, query: str) -> bool:
        """Return True if *query* contains this pattern."""
        return bool(self._compiled.search(query))


@dataclass
class WatchedResult:
    """An AnalysisResult paired with the watchlist labels that matched it."""

    result: AnalysisResult
    matched_labels: List[str]


def build_watchlist(patterns: List[dict]) -> List[WatchlistEntry]:
    """Build a list of WatchlistEntry objects from plain dicts.

    Each dict must have a ``pattern`` key and an optional ``label`` key.
    """
    entries: List[WatchlistEntry] = []
    for item in patterns:
        pattern = item.get("pattern", "")
        if not pattern:
            continue
        label = item.get("label", pattern)
        entries.append(WatchlistEntry(pattern=pattern, label=label))
    return entries


def apply_watchlist(
    results: List[AnalysisResult],
    watchlist: List[WatchlistEntry],
) -> List[WatchedResult]:
    """Return only the results that match at least one watchlist entry.

    Each returned :class:`WatchedResult` carries the labels of every entry
    that matched.
    """
    watched: List[WatchedResult] = []
    for result in results:
        query = result.entry.query
        matched = [e.label for e in watchlist if e.matches(query)]
        if matched:
            watched.append(WatchedResult(result=result, matched_labels=matched))
    return watched


def format_watchlist_report(watched: List[WatchedResult]) -> str:
    """Return a human-readable summary of watchlist hits."""
    if not watched:
        return "No watchlist matches found."
    lines = [f"Watchlist hits: {len(watched)}", ""]
    for item in watched:
        query_preview = item.result.entry.query[:80]
        labels = ", ".join(item.matched_labels)
        duration = item.result.entry.duration
        lines.append(f"  [{labels}] ({duration:.1f}ms) {query_preview}")
    return "\n".join(lines)
