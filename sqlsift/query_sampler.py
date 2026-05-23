"""query_sampler.py — reservoir-based sampling of AnalysisResult entries."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional

from sqlsift.analyzer import AnalysisResult


@dataclass
class SampleConfig:
    sample_size: int = 100
    seed: Optional[int] = None
    slow_only: bool = False


@dataclass
class SampleReport:
    results: List[AnalysisResult] = field(default_factory=list)
    total_seen: int = 0
    sample_size: int = 0

    @property
    def count(self) -> int:
        return len(self.results)

    @property
    def coverage_ratio(self) -> float:
        if self.total_seen == 0:
            return 0.0
        return round(self.count / self.total_seen, 4)


def _reservoir_sample(
    items: List[AnalysisResult],
    k: int,
    rng: random.Random,
) -> List[AnalysisResult]:
    """Return a reservoir sample of up to *k* items."""
    reservoir: List[AnalysisResult] = []
    for i, item in enumerate(items):
        if i < k:
            reservoir.append(item)
        else:
            j = rng.randint(0, i)
            if j < k:
                reservoir[j] = item
    return reservoir


def sample_results(
    results: List[AnalysisResult],
    config: Optional[SampleConfig] = None,
) -> SampleReport:
    """Sample *results* according to *config* and return a SampleReport."""
    if config is None:
        config = SampleConfig()

    rng = random.Random(config.seed)

    candidates = (
        [r for r in results if r.is_slow] if config.slow_only else list(results)
    )

    sampled = _reservoir_sample(candidates, config.sample_size, rng)

    return SampleReport(
        results=sampled,
        total_seen=len(candidates),
        sample_size=config.sample_size,
    )
