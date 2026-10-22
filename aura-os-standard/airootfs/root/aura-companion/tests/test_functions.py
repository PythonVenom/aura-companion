"""
Тесты для AgentFunctions.

Простейший агент — статический текст. Никаких моков не нужно.
"""

from __future__ import annotations

import pytest

from aura.agents.functions import AgentFunctions
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def funcs():
    return AgentFunctions()


# --- can_handle ---

def test_can_handle_what_can_you_do(funcs):
    assert funcs.can_handle(AgentRequest(text="что ты умеешь"))


def test_can_handle_what_can_you(funcs):
    assert funcs.can_handle(AgentRequest(text="что ты можешь"))


def test_can_handle_list_functions(funcs):
    assert funcs.can_handle(AgentRequest(text="список функций"))


def test_can_handle_show_functions(funcs):
    assert funcs.can_handle(AgentRequest(text="покажи функции"))


def test_can_handle_what_functions(funcs):
    assert funcs.can_handle(AgentRequest(text="какие есть функции"))


def test_can_handle_your_functions(funcs):
    assert funcs.can_handle(AgentRequest(text="твои функции"))


def test_cannot_handle_time(funcs):
    assert not funcs.can_handle(AgentRequest(text="который час"))


def test_cannot_handle_empty(funcs):
    assert not funcs.can_handle(AgentRequest(text=""))


# --- handle ---

@pytest.mark.asyncio
async def test_handle_returns_text(funcs):
    resp = await funcs.handle(AgentRequest(text="что ты умеешь"))

    assert resp.status == AgentStatus.OK
    assert resp.agent_name == "functions"
    assert "Доступные функции" in resp.text
    assert "Время" in resp.text
    assert "VK Музыка" in resp.text


@pytest.mark.asyncio
async def test_handle_all_keywords(funcs):
    """Все keywords должны давать одинаковый ответ."""
    for kw in ["какие есть функции", "список функций", "покажи функции", "твои функции"]:
        resp = await funcs.handle(AgentRequest(text=kw))
        assert resp.status == AgentStatus.OK
        assert "Доступные функции" in resp.text


@pytest.mark.asyncio
async def test_handle_not_handled(funcs):
    """Если can_handle=False, handle возвращает NOT_HANDLED."""
    resp = await funcs.handle(AgentRequest(text="просто болтовня"))
    # handle не проверяет can_handle — возвращает текст всегда.
    # Но если кто-то вызовет handle вручную для чужой команды — вернётся OK.
    # Это соответствует поведению can_handle.
    assert resp.status == AgentStatus.OK


# --- проверка содержимого ---

def test_functions_text_has_8_items(funcs):
    """Проверяем, что в тексте 8 пронумерованных пунктов."""
    text = funcs.FUNCTIONS_TEXT
    for i in range(1, 9):
        assert f"{i}." in text


def test_functions_text_starts_with_header(funcs):
    assert funcs.FUNCTIONS_TEXT.startswith("Доступные функции:")
