"""Tests for sqlsift.formatter module."""

from sqlsift.formatter import format_group, format_summary, _truncate
from sqlsift.aggregator import QueryGroup, AggregationSummary, aggregate
from sqlsift.analyzer import AnalysisResult


def _make_result(query: str, duration_ms: float, is_slow: bool = False) -> AnalysisResult:
    return AnalysisResult(
        query=query,
        duration_ms=duration_ms,
        is_slow=is_slow,
        suggestions=[],
    )


def _make_group(pattern: str, durations, slow_flags=None) -> QueryGroup:
    group = QueryGroup(pattern=pattern)
    if slow_flags is None:
        slow_flags = [False] * len(durations)
    group.results = [
        _make_result(pattern, d, s) for d, s in zip(durations, slow_flags)
    ]
    return group


class TestTruncate:
    def test_short_string_unchanged(self):
        assert _truncate("short") == "short"

    def test_long_string_truncated(self):
        long_str = "A" * 100
        result = _truncate(long_str, max_len=10)
        assert len(result) == 10
        assert result.endswith("...")

    def test_exact_length_unchanged(self):
        s = "A" * 55
        assert _truncate(s) == s


class TestFormatGroup:
    def test_contains_pattern(self):
        group = _make_group("SELECT * FROM USERS", [100, 200])
        output = format_group(group)
        assert "SELECT * FROM USERS" in output

    def test_contains_occurrence_count(self):
        group = _make_group("SELECT * FROM USERS", [100, 200])
        output = format_group(group)
        assert "2" in output

    def test_contains_avg_duration(self):
        group = _make_group("SELECT * FROM USERS", [100, 300])
        output = format_group(group)
        assert "200.00" in output

    def test_rank_prefix_present(self):
        group = _make_group("SELECT * FROM USERS", [100])
        output = format_group(group, rank=3)
        assert "#3" in output

    def test_no_rank_prefix_absent(self):
        group = _make_group("SELECT * FROM USERS", [100])
        output = format_group(group)
        assert "#" not in output

    def test_slow_count_shown(self):
        group = _make_group("SELECT * FROM USERS", [100, 600], slow_flags=[False, True])
        output = format_group(group)
        assert "1" in output


class TestFormatSummary:
    def _build_summary(self):
        results = [
            _make_result("SELECT * FROM users", 100, False),
            _make_result("SELECT * FROM users", 700, True),
            _make_result("SELECT * FROM orders", 500, True),
        ]
        return aggregate(results)

    def test_contains_total_queries(self):
        summary = self._build_summary()
        output = format_summary(summary)
        assert "3" in output

    def test_contains_slow_ratio(self):
        summary = self._build_summary()
        output = format_summary(summary)
        assert "%" in output

    def test_top_n_limits_output(self):
        results = [_make_result(f"SELECT * FROM table{i}", 100 * i) for i in range(1, 10)]
        summary = aggregate(results)
        output = format_summary(summary, top_n=3)
        assert "#3" in output
        assert "#4" not in output

    def test_header_present(self):
        summary = self._build_summary()
        output = format_summary(summary)
        assert "SQLSift Aggregation Summary" in output
