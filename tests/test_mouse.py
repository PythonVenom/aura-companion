"""
Тесты для AgentMouse.

Мок pyautogui. Живой ввод не делаем.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.mouse import AgentMouse
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def mouse():
    with patch("aura.agents.mouse._detect_wayland", return_value=False):
        with patch("pyautogui.screenshot"):
            m = AgentMouse()
    m.ready = True
    m.pyautogui = MagicMock()
    return m


@pytest.fixture
def mouse_wayland():
    with patch("aura.agents.mouse._detect_wayland", return_value=True):
        return AgentMouse()


def test_can_handle_click(mouse):
    assert mouse.can_handle(AgentRequest(text="кликни по кнопке"))


def test_can_handle_press(mouse):
    assert mouse.can_handle(AgentRequest(text="нажми клавишу enter"))


def test_can_handle_type(mouse):
    assert mouse.can_handle(AgentRequest(text="набери привет"))


def test_cannot_handle_time(mouse):
    assert not mouse.can_handle(AgentRequest(text="который час"))


def test_click_on_text_found(mouse):
    mouse.pyautogui.locateOnScreen.return_value = (100, 200, 50, 20)
    result = mouse.click_on_text("OK")
    assert "Кликнула" in result
    assert mouse.pyautogui.click.called


def test_click_on_text_not_found(mouse):
    mouse.pyautogui.locateOnScreen.return_value = None
    result = mouse.click_on_text("Nope")
    assert "Не нашла" in result


def test_click_at(mouse):
    result = mouse.click_at(10, 20)
    assert "10" in result and "20" in result


def test_type_text(mouse):
    result = mouse.type_text("hello")
    assert "hello" in result
    mouse.pyautogui.typewrite.assert_called_with("hello", interval=0.1)


def test_press_key(mouse):
    result = mouse.press_key("enter")
    assert "enter" in result


def test_extract_after(mouse):
    assert mouse._extract_after("кликни по кнопке", ("кликни по",)) == "кнопке"


def test_extract_after_empty(mouse):
    assert mouse._extract_after("привет", ("кликни по",)) == ""


@pytest.mark.asyncio
async def test_handle_click(mouse):
    mouse.pyautogui.locateOnScreen.return_value = (100, 200, 50, 20)
    resp = await mouse.handle(AgentRequest(text="кликни по кнопке"))
    assert resp.status == AgentStatus.OK
    assert "Кликнула" in resp.text


@pytest.mark.asyncio
async def test_handle_click_empty(mouse):
    resp = await mouse.handle(AgentRequest(text="кликни"))
    assert resp.status == AgentStatus.OK
    assert "Что кликнуть" in resp.text


@pytest.mark.asyncio
async def test_handle_press(mouse):
    resp = await mouse.handle(AgentRequest(text="нажми клавишу enter"))
    assert resp.status == AgentStatus.OK
    assert "enter" in resp.text


@pytest.mark.asyncio
async def test_handle_type(mouse):
    resp = await mouse.handle(AgentRequest(text="набери привет"))
    assert resp.status == AgentStatus.OK
    assert "привет" in resp.text


@pytest.mark.asyncio
async def test_handle_not_ready(mouse):
    mouse.ready = False
    resp = await mouse.handle(AgentRequest(text="кликни по кнопке"))
    assert "pyautogui не установлен" in resp.text


@pytest.mark.asyncio
async def test_handle_not_handled(mouse):
    resp = await mouse.handle(AgentRequest(text="просто болтовня"))
    assert resp.status == AgentStatus.NOT_HANDLED


def test_wayland_flag(mouse, mouse_wayland):
    assert mouse.is_wayland is False
    assert mouse_wayland.is_wayland is True
    assert mouse_wayland.ready is False
