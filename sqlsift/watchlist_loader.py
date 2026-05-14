"""Load watchlist configuration from JSON or plain-text files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from sqlsift.watchlist import WatchlistEntry, build_watchlist


def load_from_json(path: str | Path) -> List[WatchlistEntry]:
    """Load watchlist entries from a JSON file.

    The file must contain a JSON array of objects with at least a
    ``pattern`` key and an optional ``label`` key::

        [
          {"pattern": "SELECT \\\\*", "label": "star-select"},
          {"pattern": "LIKE '%", "label": "leading-wildcard"}
        ]
    """
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}, got {type(data).__name__}")
    return build_watchlist(data)


def load_from_text(path: str | Path) -> List[WatchlistEntry]:
    """Load watchlist entries from a plain-text file.

    Each non-empty, non-comment line is treated as a regex pattern.  Lines
    starting with ``#`` are ignored.  An optional label may be appended
    after a ``|`` separator::

        SELECT \\*|star-select
        LIKE '%|leading-wildcard
        # this line is a comment
        JOIN
    """
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    patterns: List[dict] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "|" in stripped:
            pattern, _, label = stripped.partition("|")
            patterns.append({"pattern": pattern.strip(), "label": label.strip()})
        else:
            patterns.append({"pattern": stripped})
    return build_watchlist(patterns)


def load_watchlist(path: str | Path) -> List[WatchlistEntry]:
    """Auto-detect format by file extension and delegate to the right loader.

    Supports ``.json`` (JSON array) and ``.txt`` / ``.list`` (plain text).
    Raises :class:`ValueError` for unknown extensions.
    """
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".json":
        return load_from_json(p)
    if suffix in (".txt", ".list"):
        return load_from_text(p)
    raise ValueError(
        f"Unsupported watchlist file extension '{suffix}'. "
        "Use .json, .txt, or .list."
    )
