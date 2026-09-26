"""Тесты ProactiveEngine (ADR-014)."""

from __future__ import annotations

import json
import time
from unittest.mock import patch

import pytest

from aura.agents import proactive
from aura.agents.proactive import (
    ProactiveEngine,
    Trigger,
    morning_briefing_trigger,
    default_engine,
)


@pytest.fixture
def tmp_state(tmp_path, monkeypatch):
    """Изолированный state-файл."""
    p = tmp_path / "proactive.json"
    monkeypatch.setattr(proactive, "STATE_PATH", p)
    return p


# --- Trigger ---

def test_trigger_defaults():
    t = Trigger(name="test", priority=5, cooldown_sec=60)
    assert t.name == "test"
    assert t.priority == 5
    assert t.cooldown_sec == 60


# --- ProactiveEngine ---

def test_register_sorts_by_priority(tmp_state):
    e = ProactiveEngine()
    e.register(Trigger(name="a", priority=1, cooldown_sec=60))
    e.register(Trigger(name="b", priority=10, cooldown_sec=60))
    e.register(Trigger(name="c", priority=5, cooldown_sec=60))
    assert e.triggers[0].name == "b"
    assert e.triggers[1].name == "c"
    assert e.triggers[2].name == "a"


def test_check_no_triggers(tmp_state):
    e = ProactiveEngine()
    assert e.check() is None


def test_check_returns_none_before_interval(tmp_state):
    e = ProactiveEngine()
    called = {"n": 0}

    def cond(state):
        called["n"] += 1
        return True

    e.register(Trigger(name="t", priority=1, cooldown_sec=60,
                       condition=cond, action=lambda: "test"))
    assert e.check() == "test"
    assert e.check() is None
    assert called["n"] == 1


def test_check_returns_action_text(tmp_state):
    e = ProactiveEngine()
    e.register(Trigger(name="t", priority=1, cooldown_sec=60,
                       condition=lambda s: True, action=lambda: "привет"))
    assert e.check() == "привет"


def test_cooldown_blocks_repeat(tmp_state):
    e = ProactiveEngine()
    e.register(Trigger(name="t", priority=1, cooldown_sec=3600,
                       condition=lambda s: True, action=lambda: "x"))
    assert e.check() == "x"
    e._last_check = 0
    assert e.check() is None


def test_condition_exception_skipped(tmp_state):
    e = ProactiveEngine()

    def bad(state):
        raise RuntimeError("boom")

    e.register(Trigger(name="bad", priority=10, cooldown_sec=60,
                       condition=bad, action=lambda: "x"))
    e.register(Trigger(name="good", priority=1, cooldown_sec=60,
                       condition=lambda s: True, action=lambda: "y"))
    assert e.check() == "y"


def test_priority_picks_higher(tmp_state):
    e = ProactiveEngine()
    e.register(Trigger(name="low", priority=1, cooldown_sec=60,
                       condition=lambda s: True, action=lambda: "low"))
    e.register(Trigger(name="high", priority=10, cooldown_sec=60,
                       condition=lambda s: True, action=lambda: "high"))
    assert e.check() == "high"


# --- morning_briefing_trigger ---

def test_morning_trigger_in_window(tmp_state):
    from datetime import datetime
    t = morning_briefing_trigger()

    class FakeDT:
        @classmethod
        def now(cls):
            return datetime(2026, 9, 26, 8, 0)

    with patch("aura.agents.proactive.datetime", FakeDT):
        state = {}
        assert t.condition(state) is True
        assert t.condition(state) is False


def test_morning_trigger_outside_window(tmp_state):
    from datetime import datetime
    t = morning_briefing_trigger()

    class FakeDT:
        @classmethod
        def now(cls):
            return datetime(2026, 9, 26, 15, 0)

    with patch("aura.agents.proactive.datetime", FakeDT):
        assert t.condition({}) is False


# --- default_engine ---

def test_default_engine_has_morning(tmp_state):
    e = default_engine()
    names = [t.name for t in e.triggers]
    assert "morning_briefing" in names


# --- state persistence ---

def test_state_persists(tmp_state):
    e = ProactiveEngine()
    e.register(Trigger(name="t", priority=1, cooldown_sec=60,
                       condition=lambda s: True, action=lambda: "x"))
    e.check()
    data = json.loads(tmp_state.read_text(encoding="utf-8"))
    assert "t" in data

