"""Tests for sqlsift.tagger."""

from sqlsift.scorer import Severity, ScoredResult
from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.tagger import (
    tag_result,
    tag_results,
    TaggedResult,
    TAG_SLOW,
    TAG_CRITICAL,
    TAG_FULL_SCAN,
    TAG_NO_INDEX,
    TAG_SELECT_STAR,
    TAG_SUBQUERY,
    TAG_LARGE_OFFSET,
    TAG_WILDCARD,
)


def _make_scored(query: str, duration: float, suggestions=None, severity=Severity.LOW):
    entry = QueryEntry(timestamp="2024-01-01T00:00:00", duration=duration, query=query)
    result = AnalysisResult(
        entry=entry,
        is_slow=duration >= 1.0,
        suggestions=suggestions or [],
    )
    return ScoredResult(result=result, score=0.0, severity=severity)


class TestTagResult:
    def test_returns_tagged_result_instance(self):
        scored = _make_scored("SELECT id FROM users WHERE id=1", 0.1)
        tagged = tag_result(scored)
        assert isinstance(tagged, TaggedResult)

    def test_fast_low_severity_has_no_slow_tag(self):
        scored = _make_scored("SELECT id FROM users WHERE id=1", 0.1, severity=Severity.LOW)
        tagged = tag_result(scored)
        assert TAG_SLOW not in tagged.tags

    def test_high_severity_gets_slow_tag(self):
        scored = _make_scored("SELECT id FROM users WHERE id=1", 5.0, severity=Severity.HIGH)
        tagged = tag_result(scored)
        assert TAG_SLOW in tagged.tags

    def test_critical_severity_gets_both_slow_and_critical_tags(self):
        scored = _make_scored("SELECT id FROM users", 10.0, severity=Severity.CRITICAL)
        tagged = tag_result(scored)
        assert TAG_SLOW in tagged.tags
        assert TAG_CRITICAL in tagged.tags

    def test_select_star_query_gets_tag(self):
        scored = _make_scored("SELECT * FROM orders WHERE id=1", 0.5)
        tagged = tag_result(scored)
        assert TAG_SELECT_STAR in tagged.tags

    def test_query_without_where_gets_full_scan_tag(self):
        scored = _make_scored("SELECT id FROM users", 0.5)
        tagged = tag_result(scored)
        assert TAG_FULL_SCAN in tagged.tags

    def test_not_in_query_gets_no_index_tag(self):
        scored = _make_scored("SELECT id FROM users WHERE id NOT IN (1,2,3)", 0.5)
        tagged = tag_result(scored)
        assert TAG_NO_INDEX in tagged.tags

    def test_like_wildcard_prefix_gets_wildcard_tag(self):
        scored = _make_scored("SELECT id FROM users WHERE name LIKE '%smith'", 0.5)
        tagged = tag_result(scored)
        assert TAG_WILDCARD in tagged.tags

    def test_subquery_gets_subquery_tag(self):
        scored = _make_scored(
            "SELECT id FROM users WHERE dept_id IN (SELECT id FROM depts)", 0.5
        )
        tagged = tag_result(scored)
        assert TAG_SUBQUERY in tagged.tags

    def test_large_offset_gets_tag(self):
        scored = _make_scored("SELECT id FROM users LIMIT 10 OFFSET 5000", 0.5)
        tagged = tag_result(scored)
        assert TAG_LARGE_OFFSET in tagged.tags

    def test_small_offset_does_not_get_tag(self):
        scored = _make_scored("SELECT id FROM users LIMIT 10 OFFSET 10", 0.5)
        tagged = tag_result(scored)
        assert TAG_LARGE_OFFSET not in tagged.tags

    def test_no_duplicate_tags(self):
        scored = _make_scored("SELECT * FROM users", 5.0, severity=Severity.HIGH)
        tagged = tag_result(scored)
        assert len(tagged.tags) == len(set(tagged.tags))


class TestTagResults:
    def test_empty_input_returns_empty_list(self):
        assert tag_results([]) == []

    def test_all_results_tagged(self):
        results = [
            _make_scored("SELECT id FROM a", 0.1),
            _make_scored("SELECT * FROM b", 2.0, severity=Severity.HIGH),
        ]
        tagged = tag_results(results)
        assert len(tagged) == 2
        assert all(isinstance(t, TaggedResult) for t in tagged)
