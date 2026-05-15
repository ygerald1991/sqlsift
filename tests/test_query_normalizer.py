"""Tests for sqlsift.query_normalizer."""
import pytest

from sqlsift.query_normalizer import (
    NormalizedQuery,
    normalize,
    normalize_all,
)


class TestNormalize:
    def test_returns_normalized_query_instance(self):
        result = normalize("SELECT 1")
        assert isinstance(result, NormalizedQuery)

    def test_original_preserved(self):
        sql = "SELECT id FROM users WHERE id = 42"
        result = normalize(sql)
        assert result.original == sql

    def test_numeric_literals_replaced(self):
        result = normalize("SELECT * FROM t WHERE id = 99")
        assert "99" not in result.normalized
        assert "?" in result.normalized

    def test_string_literals_replaced(self):
        result = normalize("SELECT * FROM t WHERE name = 'Alice'")
        assert "Alice" not in result.normalized
        assert "'?'" in result.normalized

    def test_whitespace_collapsed(self):
        result = normalize("SELECT   *   FROM   t")
        assert "  " not in result.normalized

    def test_normalized_is_uppercase(self):
        result = normalize("select * from users")
        assert result.normalized == result.normalized.upper()

    def test_inline_comment_stripped(self):
        result = normalize("SELECT id -- get the id\nFROM users")
        assert "--" not in result.normalized
        assert "get the id" not in result.normalized

    def test_block_comment_stripped(self):
        result = normalize("SELECT /* slow */ id FROM users")
        assert "slow" not in result.normalized

    def test_in_list_collapsed(self):
        result = normalize("SELECT * FROM t WHERE id IN (1, 2, 3, 4)")
        assert "IN (?)" in result.normalized
        assert "1, 2, 3" not in result.normalized

    def test_fingerprint_is_string(self):
        result = normalize("SELECT 1")
        assert isinstance(result.fingerprint, str)

    def test_fingerprint_max_64_chars(self):
        long_sql = "SELECT * FROM " + "a" * 200
        result = normalize(long_sql)
        assert len(result.fingerprint) <= 64

    def test_fingerprint_no_spaces(self):
        result = normalize("SELECT id FROM users")
        assert " " not in result.fingerprint

    def test_empty_string_returns_empty_normalized(self):
        result = normalize("")
        assert result.normalized == ""
        assert result.fingerprint == ""

    def test_whitespace_only_returns_empty_normalized(self):
        result = normalize("   ")
        assert result.normalized == ""

    def test_two_equivalent_queries_share_fingerprint(self):
        r1 = normalize("SELECT * FROM users WHERE id = 1")
        r2 = normalize("SELECT * FROM users WHERE id = 99")
        assert r1.fingerprint == r2.fingerprint

    def test_different_queries_differ_in_fingerprint(self):
        r1 = normalize("SELECT * FROM users")
        r2 = normalize("SELECT * FROM orders")
        assert r1.fingerprint != r2.fingerprint


class TestNormalizeAll:
    def test_empty_list_returns_empty(self):
        assert normalize_all([]) == []

    def test_returns_list_of_same_length(self):
        queries = ["SELECT 1", "SELECT 2", "SELECT 3"]
        results = normalize_all(queries)
        assert len(results) == 3

    def test_each_element_is_normalized_query(self):
        results = normalize_all(["SELECT id FROM t", "UPDATE t SET x = 1"])
        assert all(isinstance(r, NormalizedQuery) for r in results)
