"""Bug 15: контекст ответа после зачитки в Максе.

Сценарий:
1. pending_read → «да аура зачитай» → зачитала
2. FSM → awaiting_reply (chat сохраняется!)
3. «ответь ей: привет» → messenger.send_message(chat, "привет")
4. «да отправь» → finalize_send
"""

from unittest.mock import MagicMock

import aura_main


def _orch():
    o = object.__new__(aura_main.AuraOrchestrator)
    o.listener = MagicMock()
    o._say_with_duck = MagicMock()
    o.dm = MagicMock()
    o.dm.is_active.return_value = False
    o.orch = MagicMock()
    return o


def test_pending_read_yes_sets_awaiting_reply(monkeypatch):
    """После зачитки — FSM переходит в awaiting_reply, chat сохраняется."""
    o = _orch()
    monkeypatch.setattr(aura_main, "fsm_get",
        lambda: {"state": "pending_read", "chat": "Аня", "text": "привет"})
    captured = {}
    monkeypatch.setattr(aura_main, "fsm_set",
        lambda state, **kw: captured.update({"state": state, **kw}))
    monkeypatch.setattr(aura_main, "fsm_clear", lambda: captured.update({"clear": True}))

    o.listener.listen.return_value = "да зачитай"
    result = o._handle_fsm()

    assert result is True
    assert captured.get("state") == "awaiting_reply"
    assert captured.get("chat") == "Аня"
    assert "clear" not in captured


def test_awaiting_reply_sends_to_chat(monkeypatch):
    """«ответь ей: привет» → send_message(chat, "привет")"""
    o = _orch()
    monkeypatch.setattr(aura_main, "fsm_get",
        lambda: {"state": "awaiting_reply", "chat": "Аня", "text": ""})
    monkeypatch.setattr(aura_main, "fsm_clear", lambda: None)
    monkeypatch.setattr(aura_main, "fsm_set", lambda *a, **kw: None)

    fake_messenger = MagicMock()
    fake_messenger.send_message.return_value = "🌐 Ввела текст"
    monkeypatch.setattr(aura_main, "_get_agent",
        lambda o, n: fake_messenger if n == "messenger" else None)

    o.listener.listen.return_value = "ответь ей привет"
    result = o._handle_fsm()

    assert result is True
    fake_messenger.send_message.assert_called_once()
    args = fake_messenger.send_message.call_args
    assert args[0][0] == "Аня"
    assert "привет" in args[0][1].lower()


def test_awaiting_reply_cancel(monkeypatch):
    """«нет» → clear, Хорошо"""
    o = _orch()
    monkeypatch.setattr(aura_main, "fsm_get",
        lambda: {"state": "awaiting_reply", "chat": "Аня", "text": ""})
    cleared = []
    monkeypatch.setattr(aura_main, "fsm_clear", lambda: cleared.append(1))
    monkeypatch.setattr(aura_main, "fsm_set", lambda *a, **kw: None)

    o.listener.listen.return_value = "нет"
    result = o._handle_fsm()

    assert result is True
    assert cleared == [1]


def test_awaiting_reply_new_command_resets(monkeypatch):
    """«аура открой макс» → clear, return False"""
    o = _orch()
    monkeypatch.setattr(aura_main, "fsm_get",
        lambda: {"state": "awaiting_reply", "chat": "Аня", "text": ""})
    cleared = []
    monkeypatch.setattr(aura_main, "fsm_clear", lambda: cleared.append(1))
    monkeypatch.setattr(aura_main, "fsm_set", lambda *a, **kw: None)

    o.listener.listen.return_value = "аура открой макс"
    result = o._handle_fsm()

    assert result is False
    assert cleared == [1]
