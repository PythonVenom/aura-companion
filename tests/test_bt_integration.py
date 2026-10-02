"""Тесты интеграции RouteTree в orchestrator."""
from __future__ import annotations
from unittest.mock import MagicMock
import pytest


def test_route_tree_classifies_control():
    from aura.core.route_tree import build_route_tree
    r = build_route_tree().handle("пауза", {})
    assert r["route"] == "control"


def test_route_tree_classifies_open():
    from aura.core.route_tree import build_route_tree
    r = build_route_tree().handle("открой дипсик", {})
    assert r["route"] == "open"


def test_route_tree_fallback_ask():
    from aura.core.route_tree import build_route_tree
    r = build_route_tree().handle("который час", {})
    assert r["route"] == "ask"
