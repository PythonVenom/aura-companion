"""Тесты Capability Dispatcher."""
from __future__ import annotations
from aura.core import dispatcher


def test_register_and_dispatch():
    dispatcher.register("test.x", lambda a: "hello")
    ok, res = dispatcher.dispatch("test.x", {})
    assert ok is True
    assert res == "hello"


def test_missing_handler():
    ok, res = dispatcher.dispatch("nonexistent.y", {})
    assert ok is False
    assert "no handler" in res


def test_handler_exception():
    def boom(a):
        raise ValueError("boom")
    dispatcher.register("test.boom", boom)
    ok, res = dispatcher.dispatch("test.boom", {})
    assert ok is False
    assert "boom" in res


def test_list_registered():
    names = dispatcher.list_registered()
    assert "world.state" in names
    assert "context.recent" in names


def test_world_state_handler():
    ok, res = dispatcher.dispatch("world.state", {})
    assert ok is True
    assert "Окон" in res


def test_context_recent_handler():
    ok, res = dispatcher.dispatch("context.recent", {"minutes": 5})
    assert ok is True
