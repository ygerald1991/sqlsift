"""Tests for sqlsift.query_splitter."""
import pytest

from sqlsift.query_splitter import SplitResult, split_queries


class TestSplitQueries:
    def test_empty_string_returns_empty(self):
        result = split_queries("")
        assert isinstance(result, SplitResult)
        assert result.statements == []
        assert result.count == 0

    def test_whitespace_only_returns_empty(self):
        result = split_queries("   \n\t  ")
        assert result.statements == []

    def test_single_statement_no_semicolon(self):
        sql = "SELECT * FROM users"
        result = split_queries(sql)
        assert result.count == 1
        assert result.statements[0] == "SELECT * FROM users"

    def test_single_statement_with_semicolon(self):
        sql = "SELECT id FROM orders;"
        result = split_queries(sql)
        assert result.count == 1
        assert result.statements[0] == "SELECT id FROM orders"

    def test_two_statements_split_correctly(self):
        sql = "SELECT 1; SELECT 2"
        result = split_queries(sql)
        assert result.count == 2
        assert result.statements[0] == "SELECT 1"
        assert result.statements[1] == "SELECT 2"

    def test_three_statements(self):
        sql = "INSERT INTO t VALUES (1); UPDATE t SET a=2; DELETE FROM t;"
        result = split_queries(sql)
        assert result.count == 3

    def test_semicolon_inside_string_not_split(self):
        sql = "SELECT 'hello; world' FROM dual"
        result = split_queries(sql)
        assert result.count == 1
        assert "hello; world" in result.statements[0]

    def test_semicolon_inside_double_quoted_string_not_split(self):
        sql = 'SELECT "col;name" FROM t'
        result = split_queries(sql)
        assert result.count == 1

    def test_raw_text_preserved(self):
        sql = "SELECT 1; SELECT 2"
        result = split_queries(sql)
        assert result.raw == sql

    def test_trailing_whitespace_stripped(self):
        sql = "  SELECT 1  ;  SELECT 2  "
        result = split_queries(sql)
        assert result.statements[0] == "SELECT 1"
        assert result.statements[1] == "SELECT 2"

    def test_multiline_statement(self):
        sql = "SELECT\n  id,\n  name\nFROM users;"
        result = split_queries(sql)
        assert result.count == 1
        assert "FROM users" in result.statements[0]

    def test_count_property_matches_len(self):
        sql = "SELECT 1; SELECT 2; SELECT 3"
        result = split_queries(sql)
        assert result.count == len(result.statements) == 3
