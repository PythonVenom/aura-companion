"""Тесты F-035 — Onboarding agent.

Наука (Д4): Schein 2002 (cold-start), Nielsen 1993 (usability),
           Beyer 1998 (contextual inquiry).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aura.agents.onboarding import AgentOnboarding, QUESTIONS


@pytest.fixture
def agent(tmp_path, monkeypatch):
    """Свежий агент с изолированным PROFILE_FILE."""
    import aura.agents.onboarding as mod
    test_file = tmp_path / "profile.json"
    monkeypatch.setattr(mod, "PROFILE_FILE", test_file)
    return AgentOnboarding()


# === Инициализация ===

def test_questions_count():
    """10 вопросов по науке (Schein 2002)."""
    assert len(QUESTIONS) == 10


def test_agent_name():
    a = AgentOnboarding()
    assert a.name == "onboarding"


def test_triggers():
    """Стемминг (Porter 1980): триггеры — основы слов."""
    a = AgentOnboarding()
    assert "анкет" in a.TRIGGERS
    assert "профил" in a.TRIGGERS


# === can_handle ===

def test_can_handle_russian():
    from aura.core.protocol import AgentRequest
    a = AgentOnboarding()
    assert a.can_handle(AgentRequest(text="начать анкету"))
    assert a.can_handle(AgentRequest(text="профиль"))


def test_cannot_handle_other():
    from aura.core.protocol import AgentRequest
    a = AgentOnboarding()
    assert not a.can_handle(AgentRequest(text="какая погода"))


# === Жизненный цикл ===

def test_start_returns_first_question(agent):
    from aura.core.protocol import AgentRequest
    import asyncio
    r = asyncio.run(agent.handle(AgentRequest(text="начать анкету")))
    assert "[1/10]" in r.text
    assert "Как тебя называть" in r.text


def test_status_empty(agent):
    from aura.core.protocol import AgentRequest
    import asyncio
    r = asyncio.run(agent.handle(AgentRequest(text="статус")))
    assert "0/10" in r.text


def test_answer_text_saves(agent):
    from aura.core.protocol import AgentRequest
    import asyncio
    asyncio.run(agent.handle(AgentRequest(text="начать анкету")))
    r = agent.answer("Иван")
    assert "[2/10]" in r.text
    assert agent.get_profile().get("name") == "Иван"


def test_answer_multi_parses(agent):
    from aura.core.protocol import AgentRequest
    import asyncio
    asyncio.run(agent.handle(AgentRequest(text="начать анкету")))
    agent.answer("Иван")           # q1 name
    agent.answer("60-75")          # q2 age
    agent.answer("себя")           # q3 for_whom
    agent.answer("здоровье, связь") # q4 priorities (multi)
    profile = agent.get_profile()
    assert profile["priorities"] == ["здоровье", "связь"]


def test_answer_bool_parses(agent):
    from aura.core.protocol import AgentRequest
    import asyncio
    asyncio.run(agent.handle(AgentRequest(text="начать анкету")))
    for ans in ["Иван", "60-75", "себя", "здоровье", "нет", "8-10",
                "женский", "ru", "+7999", "да"]:
        agent.answer(ans)
    assert agent.is_completed()
    assert agent.get_profile().get("kids_mode") is True


# === Сброс ===

def test_reset_clears(agent):
    from aura.core.protocol import AgentRequest
    import asyncio
    asyncio.run(agent.handle(AgentRequest(text="начать анкету")))
    agent.answer("Иван")
    agent.reset()
    assert agent.get_profile() == {}
    assert not agent.is_completed()


# === Show profile ===

def test_show_profile_empty(agent):
    from aura.core.protocol import AgentRequest
    import asyncio
    r = asyncio.run(agent.handle(AgentRequest(text="профиль")))
    assert "Профиль пуст" in r.text


def test_show_profile_after_fill(agent):
    from aura.core.protocol import AgentRequest
    import asyncio
    asyncio.run(agent.handle(AgentRequest(text="начать анкету")))
    agent.answer("Иван")
    r = asyncio.run(agent.handle(AgentRequest(text="профиль")))
    assert "Иван" in r.text
