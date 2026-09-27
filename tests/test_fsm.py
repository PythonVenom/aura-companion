"""Регрессионные тесты _handle_fsm (Bug 1: порядок да/нет vs аура)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import aura_main


@pytest.fixture
def orch():
    o = object.__new__(aura_main.AuraOrchestrator)
    o.listener = MagicMock()
    o._say_with_duck = MagicMock()
    return o


def _run(orch, monkeypatch, state, text_input, fsm_text="привет из макса"):
    monkeypatch.setattr(
        aura_main, "fsm_get",
        lambda: {"state": state, "text": fsm_text, "chat": "Макс"},
    )
    cleared = []
    monkeypatch.setattr(aura_main, "fsm_clear", lambda: cleared.append(True))
    orch.listener.listen.return_value = text_input
    result = orch._handle_fsm()
    return result, cleared


def test_pending_read_yes_with_aura(orch, monkeypatch):
    """«да аура зачитай» — не сбрасываем по «аура» раньше времени."""
    result, cleared = _run(orch, monkeypatch, "pending_read", "да аура зачитай")
    assert result is True
    assert cleared == [True]
    orch._say_with_duck.assert_called_once_with("Сообщение: привет из макса")


def test_pending_read_no(orch, monkeypatch):
    result, cleared = _run(orch, monkeypatch, "pending_read", "нет")
    assert result is True
    assert cleared == [True]
    orch._say_with_duck.assert_called_once_with("Хорошо")


def test_pending_read_stop(orch, monkeypatch):
    """«стоп» в pending_read — работает как нет (регрессия от фикса Bug 1)."""
    result, cleared = _run(orch, monkeypatch, "pending_read", "стоп")
    assert result is True
    assert cleared == [True]
    orch._say_with_duck.assert_called_once_with("Хорошо")


def test_pending_read_pure_aura_resets(orch, monkeypatch):
    """Только «аура» — сброс, новая команда, без озвучки."""
    result, cleared = _run(orch, monkeypatch, "pending_read", "аура")
    assert result is False
    assert cleared == [True]
    orch._say_with_duck.assert_not_called()


def test_pending_read_garbage_repeats(orch, monkeypatch):
    result, cleared = _run(orch, monkeypatch, "pending_read", "бла бла")
    assert result is True
    assert cleared == []
    orch._say_with_duck.assert_called_once_with("Зачитать?")


def test_pending_read_da_ty_pro(orch, monkeypatch):
    """Bug 11: ASR коверкает «да аура зачитай» в «да ты про».
    Первое слово «да» — подтверждение, даже если остальное мусор."""
    result, cleared = _run(orch, monkeypatch, "pending_read", "да ты про")
    assert result is True
    assert cleared == [True]
    orch._say_with_duck.assert_called_once_with("Сообщение: привет из макса")


def test_pending_read_net_chto_to(orch, monkeypatch):
    """«нет что-то» — отказ по первому слову."""
    result, cleared = _run(orch, monkeypatch, "pending_read", "нет что то не то")
    assert result is True
    assert cleared == [True]
    orch._say_with_duck.assert_called_once_with("Хорошо")


def test_pending_read_short_net(orch, monkeypatch):
    result, cleared = _run(orch, monkeypatch, "pending_read", "нет")
    assert result is True
    assert cleared == [True]
    orch._say_with_duck.assert_called_once_with("Хорошо")
