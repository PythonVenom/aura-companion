"""Тесты интеграции RouteTree в orchestrator (v3.0: 7 листьев)."""
from __future__ import annotations


def test_route_tree_classifies_control():
    from aura.core.route_tree import build_route_tree
    r = build_route_tree().handle("пауза", {})
    assert r["route"] == "control"


def test_route_tree_classifies_app():
    from aura.core.route_tree import build_route_tree
    r = build_route_tree().handle("открой дипсик", {})
    assert r["route"] == "app"
    assert r["action"] == "launch"


def test_route_tree_classifies_time():
    from aura.core.route_tree import build_route_tree
    r = build_route_tree().handle("который час", {})
    assert r["route"] == "time"
    assert r["action"] == "now"


def test_route_tree_fallback_ask():
    from aura.core.route_tree import build_route_tree
    r = build_route_tree().handle("расскажи анекдот", {})
    assert r["route"] == "ask"
