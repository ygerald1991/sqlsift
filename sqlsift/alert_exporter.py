"""Export AlertReport to JSON or plain text for downstream consumption."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from sqlsift.alerter import Alert, AlertReport


def alert_to_dict(alert: Alert) -> Dict[str, Any]:
    """Serialize a single Alert to a plain dictionary."""
    return {
        "query": alert.query,
        "duration_ms": alert.duration_ms,
        "threshold_ms": alert.threshold_ms,
        "severity": alert.severity.value,
        "suggestions": list(alert.suggestions),
        "table": alert.table,
        "message": alert.message,
    }


def export_alerts_json(report: AlertReport, indent: int = 2) -> str:
    """Return the AlertReport serialized as a JSON string."""
    payload: Dict[str, Any] = {
        "total": report.count,
        "alerts": [alert_to_dict(a) for a in report.alerts],
    }
    return json.dumps(payload, indent=indent)


def export_alerts_text(report: AlertReport) -> str:
    """Return the AlertReport as a plain-text summary suitable for logs."""
    if not report.alerts:
        return "No alerts generated."
    lines: List[str] = [f"=== Alert Report ({report.count} alerts) ==="]
    for i, alert in enumerate(report.alerts, start=1):
        lines.append(f"{i}. {alert.message}")
        if alert.suggestions:
            for s in alert.suggestions:
                lines.append(f"   Suggestion: {s}")
    return "\n".join(lines)


def export_alerts(report: AlertReport, fmt: str = "json") -> str:
    """Dispatch to the appropriate exporter based on *fmt* ('json' or 'text')."""
    if fmt == "text":
        return export_alerts_text(report)
    if fmt == "json":
        return export_alerts_json(report)
    raise ValueError(f"Unsupported format: {fmt!r}. Choose 'json' or 'text'.")
