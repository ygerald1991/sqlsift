"""Format PatternReport and PatternFinding objects for human-readable output."""

from __future__ import annotations

from sqlsift.pattern_detector import PatternFinding, PatternReport

_MAX_QUERY_LEN = 80
_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _truncate(text: str, max_len: int = _MAX_QUERY_LEN) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def format_finding(finding: PatternFinding) -> str:
    """Return a single-line summary for a PatternFinding."""
    tag = f"[{finding.severity.upper()}]"
    query_snippet = _truncate(finding.query)
    return f"{tag} {finding.pattern_id}: {finding.description} | query: {query_snippet}"


def format_pattern_report(report: PatternReport) -> str:
    """Return a multi-line formatted report of all pattern findings."""
    if not report.findings:
        return "No anti-patterns detected."

    lines = [f"Pattern Report ({report.count} finding(s)):", ""]

    sorted_findings = sorted(
        report.findings,
        key=lambda f: (_SEVERITY_ORDER.get(f.severity, 99), f.pattern_id),
    )

    for finding in sorted_findings:
        lines.append(f"  {format_finding(finding)}")

    high = len(report.by_severity("high"))
    medium = len(report.by_severity("medium"))
    low = len(report.by_severity("low"))

    lines += [
        "",
        f"Summary: high={high}  medium={medium}  low={low}",
    ]
    return "\n".join(lines)
