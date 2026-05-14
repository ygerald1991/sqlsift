"""Pipeline: orchestrate parsing, analysis, scoring, and summarization."""

from dataclasses import dataclass, field
from typing import List, Optional

from sqlsift.analyzer import AnalysisResult, analyze_entries
from sqlsift.filter import FilterCriteria, filter_results
from sqlsift.parser import QueryEntry, parse_log
from sqlsift.reporter import Report, build_report
from sqlsift.scorer import ScoredResult, score_results
from sqlsift.sorter import SortKey, sort_results
from sqlsift.summarizer import RunSummary, build_summary


@dataclass
class PipelineConfig:
    slow_threshold_ms: float = 1000.0
    filter_criteria: Optional[FilterCriteria] = None
    sort_key: SortKey = SortKey.DURATION
    sort_ascending: bool = False


@dataclass
class PipelineResult:
    entries: List[QueryEntry] = field(default_factory=list)
    analysis: List[AnalysisResult] = field(default_factory=list)
    scored: List[ScoredResult] = field(default_factory=list)
    report: Optional[Report] = None
    summary: Optional[RunSummary] = None


def run_pipeline(log_text: str, config: Optional[PipelineConfig] = None) -> PipelineResult:
    """Run the full sqlsift pipeline on *log_text* and return a PipelineResult."""
    if config is None:
        config = PipelineConfig()

    entries = parse_log(log_text, threshold_ms=config.slow_threshold_ms)

    analysis = analyze_entries(entries)

    criteria = config.filter_criteria or FilterCriteria()
    filtered = filter_results(analysis, criteria)

    scored = score_results(filtered)
    sorted_scored = [
        sr for sr in sort_results(
            [sr.result for sr in scored],
            key=config.sort_key,
            ascending=config.sort_ascending,
        )
        # re-attach scores in sorted order
    ]
    # Preserve score metadata in sorted order
    result_order = {id(sr.result): sr for sr in scored}
    sorted_scored = [
        result_order[id(r)]
        for r in sort_results(
            [sr.result for sr in scored],
            key=config.sort_key,
            ascending=config.sort_ascending,
        )
    ]

    report = build_report(filtered)
    summary = build_summary(report, sorted_scored)

    return PipelineResult(
        entries=entries,
        analysis=filtered,
        scored=sorted_scored,
        report=report,
        summary=summary,
    )
