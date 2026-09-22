"""
Тесты для AgentTextEditor.

Мок pyautogui. Живой pyautogui не трогаем.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.text_editor import AgentTextEditor
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def te():
    with patch("aura.agents.text_editor._detect_wayland", return_value=False):
        with patch("pyautogui.hotkey"):
            with patch("pyperclip.copy"):
                t = AgentTextEditor()
    t.ready = True
    t.pyautogui = MagicMock()
    t.pyperclip = MagicMock()
    return t


@pytest.fixture
def te_wayland():
    with patch("aura.agents.text_editor._detect_wayland", return_value=True):
        return AgentTextEditor()


def test_can_handle_select_all(te):
    assert te.can_handle(AgentRequest(text="выдели всё"))


def test_can_handle_copy(te):
    assert te.can_handle(AgentRequest(text="копируй"))


def test_can_handle_paste(te):
    assert te.can_handle(AgentRequest(text="вставь"))


def test_can_handle_save(te):
    assert te.can_handle(AgentRequest(text="сохрани файл"))


def test_can_handle_undo(te):
    assert te.can_handle(AgentRequest(text="отмени"))


def test_cannot_handle_time(te):
    assert not te.can_handle(AgentRequest(text="который час"))


@pytest.mark.asyncio
async def test_handle_select_all(te):
    resp = await te.handle(AgentRequest(text="выдели всё"))
    assert resp.status == AgentStatus.OK
    assert "Выделила" in resp.text
    te.pyautogui.hotkey.assert_called_with("ctrl", "a")


@pytest.mark.asyncio
async def test_handle_copy(te):
    resp = await te.handle(AgentRequest(text="копируй"))
    assert "Скопировала" in resp.text
    te.pyautogui.hotkey.assert_called_with("ctrl", "c")


@pytest.mark.asyncio
async def test_handle_paste(te):
    resp = await te.handle(AgentRequest(text="вставь"))
    assert "Вставила" in resp.text
    te.pyautogui.hotkey.assert_called_with("ctrl", "v")


@pytest.mark.asyncio
async def test_handle_save(te):
    resp = await te.handle(AgentRequest(text="сохрани файл"))
    assert "Сохранила" in resp.text
    te.pyautogui.hotkey.assert_called_with("ctrl", "s")


@pytest.mark.asyncio
async def test_handle_undo(te):
    resp = await te.handle(AgentRequest(text="отмени"))
    assert "Отменила" in resp.text
    te.pyautogui.hotkey.assert_called_with("ctrl", "z")


@pytest.mark.asyncio
async def test_handle_not_ready(te):
    te.ready = False
    resp = await te.handle(AgentRequest(text="копируй"))
    assert "Установи pyautogui" in resp.text


@pytest.mark.asyncio
async def test_handle_not_handled(te):
    resp = await te.handle(AgentRequest(text="просто болтовня"))
    assert resp.status == AgentStatus.NOT_HANDLED


def test_wayland_flag(te, te_wayland):
    assert te.is_wayland is False
    assert te_wayland.is_wayland is True
    assert te_wayland.ready is False
