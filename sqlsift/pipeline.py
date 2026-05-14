"""End-to-end pipeline orchestrating parse → analyze → score → recommend."""

from dataclasses import dataclass, field
from typing import List, Optional

from sqlsift.parser import parse_log, QueryEntry
from sqlsift.analyzer import analyze_entries, AnalysisResult
from sqlsift.scorer import score_results, ScoredResult
from sqlsift.recommender import build_recommendations, RecommendationReport
from sqlsift.filter import FilterCriteria, filter_results
from sqlsift.sorter import SortKey, sort_results


@dataclass
class PipelineConfig:
    slow_threshold_ms: float = 1000.0
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    keyword_filter: Optional[str] = None
    sort_key: SortKey = SortKey.DURATION
    ascending: bool = False
    top_n: Optional[int] = None


@dataclass
class PipelineResult:
    entries: List[QueryEntry] = field(default_factory=list)
    analysis: List[AnalysisResult] = field(default_factory=list)
    scored: List[ScoredResult] = field(default_factory=list)
    recommendations: RecommendationReport = field(default_factory=RecommendationReport)
    total_parsed: int = 0
    total_slow: int = 0


def run_pipeline(log_text: str, config: Optional[PipelineConfig] = None) -> PipelineResult:
    """Run the full sqlsift pipeline on raw log text."""
    if config is None:
        config = PipelineConfig()

    entries = parse_log(log_text, threshold_ms=config.slow_threshold_ms)
    analysis = analyze_entries(entries, threshold_ms=config.slow_threshold_ms)

    criteria = FilterCriteria(
        min_duration=config.min_duration,
        max_duration=config.max_duration,
        keyword=config.keyword_filter,
    )
    filtered = filter_results(analysis, criteria)
    sorted_results = sort_results(filtered, key=config.sort_key, ascending=config.ascending)

    if config.top_n is not None:
        sorted_results = sorted_results[: config.top_n]

    scored = score_results(sorted_results)
    recommendations = build_recommendations(scored)

    total_slow = sum(1 for a in analysis if a.is_slow)

    return PipelineResult(
        entries=entries,
        analysis=sorted_results,
        scored=scored,
        recommendations=recommendations,
        total_parsed=len(entries),
        total_slow=total_slow,
    )
