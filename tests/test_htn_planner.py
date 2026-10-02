"""Тесты HTN Planner."""
from __future__ import annotations
from aura.core.htn_planner import Operator, Method, Planner, build_default_methods


def test_empty_planner():
    p = Planner()
    assert p.all_methods() == []


def test_add_and_find():
    p = Planner()
    p.add_method(Method("test", ["напиши"], [Operator("x.y")]))
    m = p.find_method("напиши сайт")
    assert m is not None
    assert m.name == "test"


def test_no_match():
    p = Planner()
    p.add_method(Method("test", ["напиши"], []))
    assert p.find_method("бла бла") is None


def test_plan_returns_operators():
    p = build_default_methods()
    ops = p.plan("что в системе")
    assert len(ops) >= 2
    assert any(o.capability == "world.state" for o in ops)


def test_plan_open_target():
    p = build_default_methods()
    ops = p.plan("открой дипсик")
    assert len(ops) >= 1


def test_plan_morning_briefing():
    p = build_default_methods()
    ops = p.plan("брифинг")
    assert len(ops) == 3


def test_plan_no_match():
    p = build_default_methods()
    assert p.plan("бла бла") == []


def test_operator_fields():
    o = Operator("x.y", {"a": 1}, "test")
    assert o.capability == "x.y"
    assert o.args == {"a": 1}
    assert o.description == "test"


def test_singleton():
    from aura.core.htn_planner import get_planner
    assert get_planner() is get_planner()
