"""Тесты Capability Graph."""
from __future__ import annotations
from aura.core.capability_graph import Capability, CapabilityGraph, build_default_graph


def test_empty_graph():
    g = CapabilityGraph()
    assert g.all_names() == []


def test_add_get():
    g = CapabilityGraph()
    g.add(Capability("x.y", "test"))
    assert g.get("x.y").name == "x.y"
    assert g.get("nope") is None


def test_default_graph_nonempty():
    g = build_default_graph()
    assert len(g.all_names()) >= 20


def test_by_tag():
    g = build_default_graph()
    care = g.by_tag("care")
    assert len(care) >= 3


def test_danger_tag():
    g = build_default_graph()
    danger = g.by_tag("danger")
    assert any(c.name == "power.shutdown" for c in danger)
    assert any(c.name == "control.kill" for c in danger)


def test_find_for():
    g = build_default_graph()
    music = g.find_for("music.")
    assert len(music) >= 3


def test_all_names_sorted():
    g = build_default_graph()
    n = g.all_names()
    assert n == sorted(n)


def test_singleton():
    from aura.core.capability_graph import get_graph
    assert get_graph() is get_graph()
