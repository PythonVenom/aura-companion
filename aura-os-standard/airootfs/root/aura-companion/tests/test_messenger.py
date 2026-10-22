"""Тесты AgentMessenger. Firefox не трогаем — mock bridge."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aura.agents.messenger import AgentMessenger
from aura.core.protocol import AgentRequest, AgentStatus


def _make(replies):
    """Агент + список ответов от send_command."""
    a = AgentMessenger()
    it = iter(replies)
    return a, lambda cmd, timeout=5.0: next(it)


# --- can_handle ---

def test_can_handle_open():
    a = AgentMessenger()
    assert a.can_handle(AgentRequest(text="аура открой макс"))


def test_can_handle_list():
    a = AgentMessenger()
    assert a.can_handle(AgentRequest(text="какие чаты в максе"))


def test_can_handle_find():
    a = AgentMessenger()
    assert a.can_handle(AgentRequest(text="найди чат с иваном"))


def test_can_handle_send():
    a = AgentMessenger()
    assert a.can_handle(AgentRequest(text="напиши в макс маме: привет"))


def test_can_handle_chat_without_max():
    """«найди чат X» — наше, даже без «макс»."""
    a = AgentMessenger()
    assert a.can_handle(AgentRequest(text="найди чат с иваном"))


def test_cannot_handle_time():
    a = AgentMessenger()
    assert not a.can_handle(AgentRequest(text="который час"))


# --- handle: list ---

@pytest.mark.asyncio
async def test_handle_list_chats():
    a = AgentMessenger()
    reply = {"ok": True, "data": {"count": 2, "chats": [
        {"name": "Иван Зеленин"}, {"name": "Петруха Чип"},
    ]}}
    with patch("aura.agents.messenger.send_command", side_effect=lambda c, t=5.0: reply):
        resp = await a.handle(AgentRequest(text="какие чаты в максе"))
    assert "Иван" in resp.text
    assert "Петруха" in resp.text


# --- handle: find ---

@pytest.mark.asyncio
async def test_handle_find_chat():
    a = AgentMessenger()
    # Bug 57: 2 вызова — find + title (verify-after-action).
    replies = [
        {"ok": True, "data": {"found": True, "name": "Иван Зеленин"}},
        {"ok": True, "data": {"title": "Иван Зеленин"}},
    ]
    it = iter(replies)
    with patch("aura.agents.messenger.send_command", side_effect=lambda c, t=5.0: next(it)):
        resp = await a.handle(AgentRequest(text="аура найди чат с иваном в максе"))
    assert "Иван" in resp.text


@pytest.mark.asyncio
async def test_handle_find_not_found():
    a = AgentMessenger()
    reply = {"ok": True, "data": {"found": False}}
    with patch("aura.agents.messenger.send_command", side_effect=lambda c, t=5.0: reply):
        resp = await a.handle(AgentRequest(text="аура найди чат с кактусом в максе"))
    assert "не найден" in resp.text.lower()


# --- handle: read ---

@pytest.mark.asyncio
async def test_handle_read_last():
    a = AgentMessenger()
    reply = {"ok": True, "data": {"last": "Привет, как дела?"}}
    with patch("aura.agents.messenger.send_command", side_effect=lambda c, t=5.0: reply):
        resp = await a.handle(AgentRequest(text="что написали в максе"))
    assert "Привет" in resp.text


# --- handle: send ---

@pytest.mark.asyncio
async def test_handle_send_message():
    a = AgentMessenger()
    # Три вызова: title + find + send (Bug 55).
    replies = [
        {"ok": True, "data": {"title": ""}},   # title — пусто, чат не открыт
        {"ok": True, "data": {"found": True, "name": "Иван"}},
        {"ok": True, "data": {"typed": True}},
    ]
    it = iter(replies)
    with patch("aura.agents.messenger.send_command", side_effect=lambda c, t=5.0: next(it)):
        resp = await a.handle(AgentRequest(text="аура напиши в макс иван: привет"))
    assert "ввела" in resp.text.lower() or "открыла" in resp.text.lower()


@pytest.mark.asyncio
async def test_handle_not_handled():
    a = AgentMessenger()
    resp = await a.handle(AgentRequest(text="просто болтовня"))
    assert resp.status == AgentStatus.NOT_HANDLED


# --- парсеры ---

def test_extract_chat_name():
    a = AgentMessenger()
    assert a._extract_chat_name("найди чат с иваном") == "иваном"


def test_extract_chat_name_empty():
    a = AgentMessenger()
    assert a._extract_chat_name("найди чат") == ""


def test_extract_send_colon():
    a = AgentMessenger()
    chat, msg = a._extract_send("напиши в макс маме: привет")
    assert chat == "маме"
    assert msg == "привет"


def test_extract_send_no_colon():
    a = AgentMessenger()
    chat, msg = a._extract_send("напиши в макс маме")
    assert chat == "маме"
    assert msg == ""


# --- bridge error ---

@pytest.mark.asyncio
async def test_handle_bridge_error():
    a = AgentMessenger()
    reply = {"error": "max tab not found"}
    with patch("aura.agents.messenger.send_command", side_effect=lambda c, t=5.0: reply):
        resp = await a.handle(AgentRequest(text="какие чаты в максе"))
    assert "макс" in resp.text.lower() or "вкладка" in resp.text.lower()


# --- Фаза 13.3: отправка и отмена ---

@pytest.mark.asyncio
async def test_handle_finalize_send():
    a = AgentMessenger()
    reply = {"ok": True, "data": {"sent": True}}
    with patch("aura.agents.messenger.send_command", side_effect=lambda c, t=5.0: reply):
        resp = await a.handle(AgentRequest(text="аура отправь в макс"))
    assert "отправила" in resp.text.lower()


@pytest.mark.asyncio
async def test_handle_clear_input():
    a = AgentMessenger()
    reply = {"ok": True, "data": {"cleared": True}}
    with patch("aura.agents.messenger.send_command", side_effect=lambda c, t=5.0: reply):
        resp = await a.handle(AgentRequest(text="аура отмени в макс"))
    assert "очистила" in resp.text.lower()


@pytest.mark.asyncio
async def test_handle_finalize_error():
    a = AgentMessenger()
    reply = {"ok": True, "data": {"sent": False, "error": "no input"}}
    with patch("aura.agents.messenger.send_command", side_effect=lambda c, t=5.0: reply):
        resp = await a.handle(AgentRequest(text="аура отправь в макс"))
    assert "не удалось" in resp.text.lower()
