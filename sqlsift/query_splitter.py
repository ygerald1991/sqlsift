"""Split a multi-statement SQL log chunk into individual query strings."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List


# Statements are separated by semicolons that are NOT inside string literals.
_STMT_RE = re.compile(
    r"(?:'[^']*'|\"[^\"]*\"|[^;])+",
    re.DOTALL,
)


@dataclass(frozen=True)
class SplitResult:
    """Container returned by :func:`split_queries`."""

    raw: str
    statements: List[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.statements)


def _clean(stmt: str) -> str:
    """Strip surrounding whitespace and trailing semicolons."""
    return stmt.strip().rstrip(";")


def split_queries(text: str) -> SplitResult:
    """Split *text* into individual SQL statements.

    Semicolons inside single- or double-quoted strings are ignored so that
    values such as ``'hello; world'`` do not cause spurious splits.

    Parameters
    ----------
    text:
        Raw SQL text, possibly containing multiple statements.

    Returns
    -------
    SplitResult
        Immutable result holding the original text and the list of cleaned
        statement strings (empty strings are dropped).
    """
    if not text or not text.strip():
        return SplitResult(raw=text, statements=[])

    statements: List[str] = [
        _clean(m.group())
        for m in _STMT_RE.finditer(text)
        if _clean(m.group())
    ]
    return SplitResult(raw=text, statements=statements)
