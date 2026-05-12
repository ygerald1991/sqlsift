"""High-level pipeline combining filtering, sorting, and reporting."""

from dataclasses import dataclass, field
from typing import List, Optional

from sqlsift.analyzer import AnalysisResult, analyze_entries
from sqlsift.filter import FilterCriteria, filter_results
from sqlsift.parser import QueryEntry
from sqlsift.reporter import Report, build_report
from sqlsift.sorter import SortKey, sort_results


@dataclass
class PipelineConfig:
    """Configuration for a full analysis pipeline run."""
    threshold_ms: float = 1000.0
    filter_criteria: FilterCriteria = field(default_factory=FilterCriteria)
    sort_key: SortKey = SortKey.DURATION
    sort_descending: bool = True
    top_n: Optional[int] = None


@dataclass
class PipelineResult:
    """Output produced by running the pipeline."""
    all_results: List[AnalysisResult]
    filtered_results: List[AnalysisResult]
    report: Report


def run_pipeline(
    entries: List[QueryEntry],
    config: Optional[PipelineConfig] = None,
) -> PipelineResult:
    """Analyse *entries*, filter, sort and build a report.

    Parameters
    ----------
    entries:
        Parsed query log entries to process.
    config:
        Optional pipeline configuration; defaults are used when omitted.

    Returns
    -------
    PipelineResult
        Contains all analysis results, the filtered/sorted subset, and a
        summary report built from the *filtered* results.
    """
    if config is None:
        config = PipelineConfig()

    all_results = analyze_entries(entries, threshold_ms=config.threshold_ms)
    filtered = filter_results(all_results, config.filter_criteria)
    sorted_results = sort_results(
        filtered,
        key=config.sort_key,
        descending=config.sort_descending,
    )

    if config.top_n is not None:
        sorted_results = sorted_results[: config.top_n]

    report = build_report(sorted_results)

    return PipelineResult(
        all_results=all_results,
        filtered_results=sorted_results,
        report=report,
    )
