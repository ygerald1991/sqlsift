"""Alert generation for queries exceeding configurable thresholds."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlsift.scorer import ScoredResult, Severity
from sqlsift.threshold import ThresholdConfig, get_threshold


@dataclass(frozen=True)
class Alert:
    query: str
    duration_ms: float
    threshold_ms: float
    severity: Severity
    suggestions: List[str]
    table: Optional[str] = None

    @property
    def message(self) -> str:
        excess = self.duration_ms - self.threshold_ms
        return (
            f"[{self.severity.value.upper()}] Query exceeded threshold by "
            f"{excess:.1f}ms ({self.duration_ms:.1f}ms > {self.threshold_ms:.1f}ms): "
            f"{self.query[:80]}"
        )


@dataclass
class AlertReport:
    alerts: List[Alert] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.alerts)

    def by_severity(self, severity: Severity) -> List[Alert]:
        return [a for a in self.alerts if a.severity == severity]


def _extract_table(query: str) -> Optional[str]:
    """Naively extract the first table name from a FROM or INTO clause."""
    tokens = query.upper().split()
    for keyword in ("FROM", "INTO", "UPDATE", "JOIN"):
        if keyword in tokens:
            idx = tokens.index(keyword)
            if idx + 1 < len(tokens):
                raw = tokens[idx + 1].strip(",;()")
                if raw and raw.isidentifier():
                    return raw.lower()
    return None


def build_alerts(
    scored: List[ScoredResult],
    config: ThresholdConfig,
) -> AlertReport:
    """Generate alerts for any scored result that exceeds its threshold."""
    report = AlertReport()
    for sr in scored:
        query = sr.result.entry.query
        table = _extract_table(query)
        threshold = get_threshold(config, table)
        if sr.result.entry.duration_ms > threshold:
            alert = Alert(
                query=query,
                duration_ms=sr.result.entry.duration_ms,
                threshold_ms=threshold,
                severity=sr.severity,
                suggestions=list(sr.result.suggestions),
                table=table,
            )
            report.alerts.append(alert)
    return report


def format_alerts(report: AlertReport) -> str:
    """Return a human-readable string for all alerts in the report."""
    if not report.alerts:
        return "No alerts."
    lines = [f"Alerts ({report.count} total):"]
    for alert in report.alerts:
        lines.append(f"  {alert.message}")
        for suggestion in alert.suggestions:
            lines.append(f"    - {suggestion}")
    return "\n".join(lines)
