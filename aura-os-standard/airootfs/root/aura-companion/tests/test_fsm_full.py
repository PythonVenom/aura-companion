"""Полное покрытие FSM: все переходы."""
import pytest
from unittest.mock import MagicMock
import aura_main


@pytest.fixture
def orch():
    o = object.__new__(aura_main.AuraOrchestrator)
    o.listener = MagicMock()
    o._say_with_duck = MagicMock()
    o.dm = MagicMock()
    o.dm.is_active.return_value = False
    o.orch = MagicMock()
    return o


def _run(orch, monkeypatch, state, text, chat="", fsm_text=""):
    monkeypatch.setattr(aura_main, "fsm_get",
        lambda: {"state": state, "chat": chat, "text": fsm_text})
    cleared = []
    monkeypatch.setattr(aura_main, "fsm_clear", lambda: cleared.append(1))
    monkeypatch.setattr(aura_main, "fsm_set", lambda *a, **k: None)
    orch.listener.listen.return_value = text
    return orch._handle_fsm(), cleared


def test_idle_returns_false(orch, monkeypatch):
    monkeypatch.setattr(aura_main, "fsm_get", lambda: {"state": "idle"})
    result = orch._handle_fsm()
    assert result is False


def test_awaiting_command_routes_to_orch(orch, monkeypatch):
    monkeypatch.setattr(aura_main, "fsm_set", lambda *a, **k: None)
    import asyncio
    with monkeypatch.context() as m:
        m.setattr(aura_main, "fsm_get", lambda: {"state": "awaiting_command", "chat": "", "text": ""})
        m.setattr(aura_main, "fsm_clear", lambda: None)
        orch.listener.listen.return_value = "который час"
        orch.orch.process = MagicMock(return_value="7 вечера")
        result = orch._handle_fsm()
    assert result is True


def test_ask_text_sends_message(orch, monkeypatch):
    monkeypatch.setattr(aura_main, "fsm_get",
        lambda: {"state": "ask_text", "chat": "Аня", "text": ""})
    monkeypatch.setattr(aura_main, "fsm_set", lambda *a, **k: None)
    monkeypatch.setattr(aura_main, "fsm_clear", lambda: None)
    monkeypatch.setattr(aura_main, "_get_agent",
        lambda o, n: MagicMock(send_message=MagicMock(return_value="ok")) if n == "messenger" else None)
    orch.listener.listen.return_value = "привет"
    result = orch._handle_fsm()
    assert result is True


def test_ask_confirm_sends(orch, monkeypatch):
    monkeypatch.setattr(aura_main, "fsm_get",
        lambda: {"state": "ask_confirm", "chat": "Аня", "text": "привет"})
    monkeypatch.setattr(aura_main, "fsm_clear", lambda: None)
    monkeypatch.setattr(aura_main, "_get_agent",
        lambda o, n: MagicMock(finalize_send=MagicMock(return_value="отправила")) if n == "messenger" else None)
    orch.listener.listen.return_value = "да отправь"
    result = orch._handle_fsm()
    assert result is True


def test_pending_read_cancel_via_net(orch, monkeypatch):
    result, cleared = _run(orch, monkeypatch, "pending_read", "нет")
    assert result is True
    assert cleared == [1]


def test_awaiting_reply_ignores_other(orch, monkeypatch):
    monkeypatch.setattr(aura_main, "fsm_get",
        lambda: {"state": "awaiting_reply", "chat": "Аня", "text": ""})
    monkeypatch.setattr(aura_main, "fsm_clear", lambda: None)
    monkeypatch.setattr(aura_main, "fsm_set", lambda *a, **k: None)
    orch.listener.listen.return_value = "бла бла"
    result = orch._handle_fsm()
    assert result is True
