"""Tag analysis results with categorical labels based on query patterns and severity."""

from dataclasses import dataclass, field
from typing import List

from sqlsift.scorer import ScoredResult, Severity


# Known tag labels
TAG_SLOW = "slow"
TAG_CRITICAL = "critical"
TAG_FULL_SCAN = "full_scan"
TAG_NO_INDEX = "no_index"
TAG_SELECT_STAR = "select_star"
TAG_SUBQUERY = "subquery"
TAG_LARGE_OFFSET = "large_offset"
TAG_WILDCARD = "wildcard"


@dataclass
class TaggedResult:
    scored: ScoredResult
    tags: List[str] = field(default_factory=list)


def _tags_from_query(query: str) -> List[str]:
    """Derive tags from the raw SQL query text."""
    tags: List[str] = []
    normalized = query.upper()

    if "SELECT *" in normalized:
        tags.append(TAG_SELECT_STAR)
    if "SELECT" in normalized and "FROM" in normalized and "WHERE" not in normalized:
        tags.append(TAG_FULL_SCAN)
    if "NOT IN" in normalized or "NOT EXISTS" in normalized:
        tags.append(TAG_NO_INDEX)
    if "LIKE '%" in normalized or "LIKE \"% " in normalized:
        tags.append(TAG_WILDCARD)
    if "OFFSET" in normalized:
        # Try to detect large offsets (> 1000)
        import re
        match = re.search(r"OFFSET\s+(\d+)", normalized)
        if match and int(match.group(1)) > 1000:
            tags.append(TAG_LARGE_OFFSET)
    if normalized.count("SELECT") > 1:
        tags.append(TAG_SUBQUERY)

    return tags


def _tags_from_severity(severity: Severity) -> List[str]:
    """Derive tags from the computed severity level."""
    tags: List[str] = []
    if severity in (Severity.HIGH, Severity.CRITICAL):
        tags.append(TAG_SLOW)
    if severity == Severity.CRITICAL:
        tags.append(TAG_CRITICAL)
    return tags


def tag_result(scored: ScoredResult) -> TaggedResult:
    """Attach tags to a single ScoredResult."""
    tags: List[str] = []
    tags.extend(_tags_from_severity(scored.severity))
    tags.extend(_tags_from_query(scored.result.entry.query))
    # Deduplicate while preserving order
    seen = set()
    unique_tags = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            unique_tags.append(t)
    return TaggedResult(scored=scored, tags=unique_tags)


def tag_results(scored_results: List[ScoredResult]) -> List[TaggedResult]:
    """Tag a list of ScoredResults."""
    return [tag_result(r) for r in scored_results]
