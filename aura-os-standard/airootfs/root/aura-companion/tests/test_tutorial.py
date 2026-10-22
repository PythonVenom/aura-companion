"""Тесты F-036 — Tutorial agent.

Наука (Д4): Fogg 2009, Nielsen 1993, Bloom 1984.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from aura.agents.tutorial import AgentTutorial, LESSONS


@pytest.fixture
def agent(tmp_path, monkeypatch):
    import aura.agents.tutorial as mod
    monkeypatch.setattr(mod, "STATE_FILE", tmp_path / "state.json")
    return AgentTutorial()


def test_lessons_count():
    assert len(LESSONS) == 5


def test_lessons_have_say():
    for l in LESSONS:
        assert "say" in l
        assert "expect" in l


def test_agent_name():
    a = AgentTutorial()
    assert a.name == "tutorial"


def test_can_handle():
    from aura.core.protocol import AgentRequest
    a = AgentTutorial()
    assert a.can_handle(AgentRequest(text="начать туториал"))
    assert not a.can_handle(AgentRequest(text="какая погода"))


def test_start_returns_lesson_1(agent):
    from aura.core.protocol import AgentRequest
    r = asyncio.run(agent.handle(AgentRequest(text="начать")))
    assert "Урок 1/5" in r.text
    assert "Аура, привет" in r.text


def test_next_advances(agent):
    from aura.core.protocol import AgentRequest
    asyncio.run(agent.handle(AgentRequest(text="начать")))
    r = agent._next()
    assert "Урок 2/5" in r.text


def test_full_completion(agent):
    asyncio.run(agent.handle(__import__("aura.core.protocol", fromlist=["AgentRequest"]).AgentRequest(text="начать")))
    for _ in range(5):
        r = agent._next()
    assert "пройден" in r.text.lower() or "Туториал" in r.text


def test_status(agent):
    from aura.core.protocol import AgentRequest
    r = asyncio.run(agent.handle(AgentRequest(text="статус")))
    assert "0/5" in r.text


def test_reset(agent):
    from aura.core.protocol import AgentRequest
    asyncio.run(agent.handle(AgentRequest(text="начать")))
    agent._next()
    agent._reset()
    r = asyncio.run(agent.handle(AgentRequest(text="статус")))
    assert "0/5" in r.text
