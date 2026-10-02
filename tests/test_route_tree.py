"""Тесты RouteTree."""
from __future__ import annotations
from aura.core.route_tree import build_route_tree


def test_control_pause():
    r = build_route_tree().handle("пауза", {})
    assert r["route"] == "control"


def test_control_panic():
    r = build_route_tree().handle("panic", {})
    assert r["route"] == "control"


def test_open_vk():
    r = build_route_tree().handle("открой вк", {})
    assert r["route"] == "open"


def test_open_deepseek():
    r = build_route_tree().handle("открой дипсик", {})
    assert r["route"] == "open"


def test_fallback_ask():
    r = build_route_tree().handle("который час", {})
    assert r["route"] == "ask"


def test_unknown_ask():
    r = build_route_tree().handle("бла бла", {})
    assert r["route"] == "ask"
