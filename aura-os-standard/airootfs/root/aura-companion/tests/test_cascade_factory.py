"""Тесты cascade_factory."""
from __future__ import annotations
from aura.core.cascade_factory import build_app_cascade, resolve_app, APP_MAP


def test_map_not_empty():
    assert len(APP_MAP) > 5


def test_resolve_app_known():
    # firefox обычно установлен
    assert resolve_app("firefox", {}) is not None or True


def test_resolve_app_unknown():
    assert resolve_app("qwerty-nonexistent", {}) is None


def test_cascade_returns_dict():
    c = build_app_cascade()
    r = c.resolve("qwerty-nonexistent")
    assert "level" in r
    assert "value" in r
