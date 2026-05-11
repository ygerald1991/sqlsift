"""Query log parser for extracting SQL queries and their execution metadata."""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QueryEntry:
    """Represents a single parsed query log entry."""

    raw_query: str
    duration_ms: float
    timestamp: Optional[str] = None
    user: Optional[str] = None
    database: Optional[str] = None
    tags: list = field(default_factory=list)

    def is_slow(self, threshold_ms: float = 1000.0) -> bool:
        """Return True if the query exceeds the given duration threshold."""
        return self.duration_ms >= threshold_ms


# Matches lines like: # Time: 2024-01-15T10:23:45 | Duration: 1234ms | Query: SELECT ...
LOG_PATTERN = re.compile(
    r"(?:# Time:\s*(?P<timestamp>[\w\-T:.]+)\s*\|\s*)?"
    r"(?:User:\s*(?P<user>\w+)\s*\|\s*)?"
    r"(?:DB:\s*(?P<database>\w+)\s*\|\s*)?"
    r"Duration:\s*(?P<duration>[\d.]+)ms\s*\|\s*Query:\s*(?P<query>.+)",
    re.IGNORECASE,
)


def parse_line(line: str) -> Optional[QueryEntry]:
    """Parse a single log line into a QueryEntry, or return None if unrecognised."""
    line = line.strip()
    if not line:
        return None

    match = LOG_PATTERN.match(line)
    if not match:
        return None

    return QueryEntry(
        raw_query=match.group("query").strip(),
        duration_ms=float(match.group("duration")),
        timestamp=match.group("timestamp"),
        user=match.group("user"),
        database=match.group("database"),
    )


def parse_log(log_text: str) -> list[QueryEntry]:
    """Parse a multi-line query log string and return all valid QueryEntry objects."""
    entries = []
    for line in log_text.splitlines():
        entry = parse_line(line)
        if entry is not None:
            entries.append(entry)
    return entries
