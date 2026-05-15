"""Normalize raw SQL queries for consistent comparison and grouping."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


# Compiled patterns for performance
_WHITESPACE = re.compile(r"\s+")
_NUMERIC_LITERAL = re.compile(r"\b\d+(\.\d+)?\b")
_STRING_LITERAL = re.compile(r"'[^']*'")
_IN_LIST = re.compile(r"IN\s*\([^)]+\)", re.IGNORECASE)
_COMMENT_INLINE = re.compile(r"--[^\n]*")
_COMMENT_BLOCK = re.compile(r"/\*.*?\*/", re.DOTALL)


@dataclass(frozen=True)
class NormalizedQuery:
    original: str
    normalized: str
    fingerprint: str

    def __str__(self) -> str:  # pragma: no cover
        return self.normalized


def _strip_comments(sql: str) -> str:
    sql = _COMMENT_BLOCK.sub(" ", sql)
    sql = _COMMENT_INLINE.sub(" ", sql)
    return sql


def _replace_literals(sql: str) -> str:
    sql = _STRING_LITERAL.sub("'?'", sql)
    sql = _NUMERIC_LITERAL.sub("?", sql)
    return sql


def _collapse_in_lists(sql: str) -> str:
    return _IN_LIST.sub("IN (?)", sql)


def _collapse_whitespace(sql: str) -> str:
    return _WHITESPACE.sub(" ", sql).strip()


def normalize(sql: str) -> NormalizedQuery:
    """Return a NormalizedQuery for the given raw SQL string."""
    if not sql or not sql.strip():
        return NormalizedQuery(original=sql, normalized="", fingerprint="")

    step = _strip_comments(sql)
    step = _collapse_whitespace(step)
    step = _replace_literals(step)
    step = _collapse_in_lists(step)
    step = _collapse_whitespace(step)
    normalized = step.upper()
    fingerprint = re.sub(r"[^A-Z0-9]", "_", normalized)[:64]
    return NormalizedQuery(original=sql, normalized=normalized, fingerprint=fingerprint)


def normalize_all(queries: List[str]) -> List[NormalizedQuery]:
    """Normalize a list of raw SQL strings."""
    return [normalize(q) for q in queries]
