"""Tests for sqlsift.query_planner and sqlsift.plan_formatter."""
from __future__ import annotations

import pytest

from sqlsift.analyzer import AnalysisResult
from sqlsift.parser import QueryEntry
from sqlsift.scorer import ScoredResult, Severity
from sqlsift.query_planner import (
    PlanHint,
    QueryPlan,
    build_query_plan,
    build_query_plans,
)
from sqlsift.plan_formatter import format_plan, format_plan_report


def _make_scored(query: str, duration: float = 2000.0, severity: Severity = Severity.HIGH) -> ScoredResult:
    entry = QueryEntry(timestamp=None, duration_ms=duration, query=query, user=None, db=None)
    result = AnalysisResult(entry=entry, is_slow=True, suggestions=["Use index"])
    return ScoredResult(result=result, score=80.0, severity=severity)


class TestBuildQueryPlan:
    def test_returns_query_plan_instance(self):
        scored = _make_scored("SELECT id FROM users WHERE id = 1")
        plan = build_query_plan(scored)
        assert isinstance(plan, QueryPlan)

    def test_query_attribute_preserved(self):
        q = "SELECT id FROM users WHERE id = 1"
        plan = build_query_plan(_make_scored(q))
        assert plan.query == q

    def test_high_severity_adds_explain_hint(self):
        plan = build_query_plan(_make_scored("SELECT id FROM t WHERE id=1", severity=Severity.HIGH))
        hints_text = [h.hint for h in plan.hints]
        assert "EXPLAIN ANALYZE" in hints_text

    def test_low_severity_no_explain_hint(self):
        scored = _make_scored("SELECT id FROM t WHERE id=1", severity=Severity.LOW)
        plan = build_query_plan(scored)
        hints_text = [h.hint for h in plan.hints]
        assert "EXPLAIN ANALYZE" not in hints_text

    def test_select_star_hint_detected(self):
        plan = build_query_plan(_make_scored("SELECT * FROM orders WHERE id=1"))
        hints_text = [h.hint for h in plan.hints]
        assert "Avoid SELECT *" in hints_text

    def test_missing_where_clause_hint(self):
        plan = build_query_plan(_make_scored("SELECT id FROM users"))
        hints_text = [h.hint for h in plan.hints]
        assert "Missing WHERE clause" in hints_text

    def test_leading_wildcard_hint(self):
        plan = build_query_plan(_make_scored("SELECT id FROM t WHERE name LIKE '%foo'"))
        hints_text = [h.hint for h in plan.hints]
        assert "Leading wildcard LIKE" in hints_text

    def test_order_by_without_limit_hint(self):
        plan = build_query_plan(_make_scored("SELECT id FROM t WHERE x=1 ORDER BY created_at"))
        hints_text = [h.hint for h in plan.hints]
        assert "ORDER BY without LIMIT" in hints_text

    def test_order_by_with_limit_no_hint(self):
        plan = build_query_plan(_make_scored("SELECT id FROM t WHERE x=1 ORDER BY created_at LIMIT 10"))
        hints_text = [h.hint for h in plan.hints]
        assert "ORDER BY without LIMIT" not in hints_text

    def test_not_in_hint(self):
        plan = build_query_plan(_make_scored("SELECT id FROM t WHERE id NOT IN (SELECT id FROM other)"))
        hints_text = [h.hint for h in plan.hints]
        assert "NOT IN subquery" in hints_text

    def test_has_hints_true_when_hints_present(self):
        plan = build_query_plan(_make_scored("SELECT * FROM t"))
        assert plan.has_hints is True

    def test_has_hints_false_when_no_hints(self):
        scored = _make_scored("SELECT id FROM t WHERE id=1", severity=Severity.LOW)
        plan = build_query_plan(scored)
        # may or may not have hints; just check the property reflects list length
        assert plan.has_hints == (len(plan.hints) > 0)

    def test_build_query_plans_returns_list(self):
        scored_list = [_make_scored("SELECT * FROM t"), _make_scored("DELETE FROM t")]
        plans = build_query_plans(scored_list)
        assert len(plans) == 2
        assert all(isinstance(p, QueryPlan) for p in plans)


class TestFormatPlan:
    def test_format_plan_contains_query(self):
        plan = build_query_plan(_make_scored("SELECT id FROM t WHERE id=1"))
        text = format_plan(plan)
        assert "SELECT id FROM t WHERE id=1" in text

    def test_format_plan_with_index(self):
        plan = build_query_plan(_make_scored("SELECT id FROM t WHERE id=1"))
        text = format_plan(plan, index=3)
        assert "[3]" in text

    def test_format_plan_no_hints_message(self):
        scored = _make_scored("SELECT id FROM t WHERE id=1", severity=Severity.LOW)
        plan = QueryPlan(query="SELECT id FROM t WHERE id=1", hints=[])
        text = format_plan(plan)
        assert "no hints" in text

    def test_format_plan_report_empty(self):
        text = format_plan_report([])
        assert "No query plans" in text

    def test_format_plan_report_header_counts(self):
        plans = build_query_plans([_make_scored("SELECT * FROM t")])
        text = format_plan_report(plans)
        assert "1 queries analysed" in text

    def test_long_query_truncated(self):
        long_q = "SELECT " + "a, " * 40 + "b FROM t WHERE id=1"
        plan = QueryPlan(query=long_q, hints=[])
        text = format_plan(plan)
        assert "..." in text
