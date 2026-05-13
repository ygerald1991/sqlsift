"""sqlsift — detect slow queries and generate optimization suggestions."""

from sqlsift.parser import QueryEntry, parse_log, parse_line, is_slow
from sqlsift.analyzer import AnalysisResult, analyze_entry, analyze_entries
from sqlsift.reporter import Report, build_report, format_report
from sqlsift.filter import FilterCriteria, filter_results, top_slowest
from sqlsift.sorter import SortKey, sort_results
from sqlsift.aggregator import QueryGroup, group_by_pattern
from sqlsift.scorer import Severity, ScoredResult, score_result, score_results
from sqlsift.pipeline import PipelineConfig, PipelineResult, run_pipeline

__all__ = [
    "QueryEntry", "parse_log", "parse_line", "is_slow",
    "AnalysisResult", "analyze_entry", "analyze_entries",
    "Report", "build_report", "format_report",
    "FilterCriteria", "filter_results", "top_slowest",
    "SortKey", "sort_results",
    "QueryGroup", "group_by_pattern",
    "Severity", "ScoredResult", "score_result", "score_results",
    "PipelineConfig", "PipelineResult", "run_pipeline",
]
