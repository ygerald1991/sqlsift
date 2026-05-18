"""Detect queries approaching or exceeding configurable timeout thresholds."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlsift.analyzer import AnalysisResult
from sqlsift.scorer import ScoredResult, Severity

_DEFAULT_TIMEOUT_MS = 5_000.0
_DEFAULT_WARNING_RATIO = 0.75  # warn when duration >= 75 % of timeout


@dataclass(frozen=True)
class TimeoutConfig:
    timeout_ms: float = _DEFAULT_TIMEOUT_MS
    warning_ratio: float = _DEFAULT_WARNING_RATIO

    def warning_threshold(self) -> float:
        return self.timeout_ms * self.warning_ratio


@dataclass
class TimeoutFlag:
    query: str
    duration_ms: float
    timeout_ms: float
    exceeded: bool
    near_timeout: bool
    severity: Severity

    @property
    def message(self) -> str:
        if self.exceeded:
            return (
                f"Query exceeded timeout ({self.duration_ms:.1f} ms "
                f"> {self.timeout_ms:.1f} ms)"
            )
        if self.near_timeout:
            pct = (self.duration_ms / self.timeout_ms) * 100
            return (
                f"Query is near timeout threshold "
                f"({self.duration_ms:.1f} ms, {pct:.0f}% of {self.timeout_ms:.1f} ms)"
            )
        return "Query is within acceptable duration"


@dataclass
class TimeoutReport:
    flags: List[TimeoutFlag] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.flags)

    @property
    def exceeded_count(self) -> int:
        return sum(1 for f in self.flags if f.exceeded)

    @property
    def near_count(self) -> int:
        return sum(1 for f in self.flags if f.near_timeout and not f.exceeded)


def _severity_for(duration_ms: float, cfg: TimeoutConfig) -> Severity:
    if duration_ms >= cfg.timeout_ms:
        return Severity.CRITICAL
    if duration_ms >= cfg.warning_threshold():
        return Severity.HIGH
    return Severity.LOW


def check_timeout(
    result: ScoredResult,
    cfg: Optional[TimeoutConfig] = None,
) -> Optional[TimeoutFlag]:
    """Return a TimeoutFlag if the query is near or over the timeout, else None."""
    cfg = cfg or TimeoutConfig()
    duration = result.result.entry.duration_ms
    exceeded = duration >= cfg.timeout_ms
    near = duration >= cfg.warning_threshold()
    if not near:
        return None
    return TimeoutFlag(
        query=result.result.entry.query,
        duration_ms=duration,
        timeout_ms=cfg.timeout_ms,
        exceeded=exceeded,
        near_timeout=near,
        severity=_severity_for(duration, cfg),
    )


def build_timeout_report(
    results: List[ScoredResult],
    cfg: Optional[TimeoutConfig] = None,
) -> TimeoutReport:
    """Build a TimeoutReport from a list of ScoredResults."""
    cfg = cfg or TimeoutConfig()
    flags = [f for r in results if (f := check_timeout(r, cfg)) is not None]
    return TimeoutReport(flags=flags)
