"""Tests for sqlsift.query_fingerprint."""
from __future__ import annotations

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.query_fingerprint import (
    Fingerprint,
    FingerprintGroup,
    fingerprint_query,
    group_by_fingerprint,
    _normalize,
)


def _make_result(query: str, duration_ms: float = 100.0) -> AnalysisResult:
    entry = QueryEntry(
        timestamp="2024-01-01T00:00:00",
        duration_ms=duration_ms,
        query=query,
        user="tester",
        database="db",
    )
    return AnalysisResult(entry=entry, is_slow=duration_ms >= 1000, suggestions=[])


class TestNormalize:
    def test_whitespace_collapsed(self):
        assert _normalize("SELECT  *   FROM   t") == "SELECT * FROM T"

    def test_numeric_literals_replaced(self):
        assert "?" in _normalize("SELECT * FROM t WHERE id = 42")

    def test_string_literals_replaced(self):
        assert "?" in _normalize("SELECT * FROM t WHERE name = 'alice'")

    def test_single_line_comment_removed(self):
        result = _normalize("SELECT 1 -- comment")
        assert "--" not in result
        assert "COMMENT" not in result

    def test_block_comment_removed(self):
        result = _normalize("SELECT /* block */ 1")
        assert "block" not in result.lower()

    def test_uppercased(self):
        result = _normalize("select * from users")
        assert result == result.upper()


class TestFingerprintQuery:
    def test_returns_fingerprint_instance(self):
        fp = fingerprint_query("SELECT * FROM t")
        assert isinstance(fp, Fingerprint)

    def test_raw_preserved(self):
        query = "SELECT * FROM t WHERE id = 1"
        fp = fingerprint_query(query)
        assert fp.raw == query

    def test_digest_is_twelve_chars(self):
        fp = fingerprint_query("SELECT 1")
        assert len(fp.digest) == 12

    def test_equivalent_queries_same_digest(self):
        fp1 = fingerprint_query("SELECT * FROM t WHERE id = 1")
        fp2 = fingerprint_query("SELECT * FROM t WHERE id = 99")
        assert fp1.digest == fp2.digest

    def test_different_queries_different_digest(self):
        fp1 = fingerprint_query("SELECT * FROM users")
        fp2 = fingerprint_query("SELECT * FROM orders")
        assert fp1.digest != fp2.digest

    def test_str_returns_digest(self):
        fp = fingerprint_query("SELECT 1")
        assert str(fp) == fp.digest


class TestGroupByFingerprint:
    def test_empty_input_returns_empty_dict(self):
        assert group_by_fingerprint([]) == {}

    def test_single_result_creates_one_group(self):
        result = _make_result("SELECT * FROM t")
        groups = group_by_fingerprint([result])
        assert len(groups) == 1

    def test_identical_queries_grouped_together(self):
        r1 = _make_result("SELECT * FROM t WHERE id = 1", 200.0)
        r2 = _make_result("SELECT * FROM t WHERE id = 2", 300.0)
        groups = group_by_fingerprint([r1, r2])
        assert len(groups) == 1
        group = next(iter(groups.values()))
        assert group.count == 2

    def test_different_queries_separate_groups(self):
        r1 = _make_result("SELECT * FROM users")
        r2 = _make_result("SELECT * FROM orders")
        groups = group_by_fingerprint([r1, r2])
        assert len(groups) == 2

    def test_avg_duration_computed(self):
        r1 = _make_result("SELECT * FROM t WHERE id = 1", 100.0)
        r2 = _make_result("SELECT * FROM t WHERE id = 2", 300.0)
        groups = group_by_fingerprint([r1, r2])
        group = next(iter(groups.values()))
        assert group.avg_duration == pytest.approx(200.0)

    def test_max_duration_computed(self):
        r1 = _make_result("SELECT * FROM t WHERE id = 1", 100.0)
        r2 = _make_result("SELECT * FROM t WHERE id = 2", 500.0)
        groups = group_by_fingerprint([r1, r2])
        group = next(iter(groups.values()))
        assert group.max_duration == pytest.approx(500.0)

    def test_group_fingerprint_attribute_set(self):
        result = _make_result("SELECT 1")
        groups = group_by_fingerprint([result])
        group = next(iter(groups.values()))
        assert isinstance(group.fingerprint, Fingerprint)
