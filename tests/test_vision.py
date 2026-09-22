"""
Тесты для AgentVision.

Мок pyautogui. Живой screenshot не делаем.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.vision import AgentVision
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def vision():
    with patch("aura.agents.vision._detect_wayland", return_value=False):
        with patch("pyautogui.screenshot"):
            v = AgentVision()
    v.ready = True
    v.pyautogui = MagicMock()
    return v


@pytest.fixture
def vision_wayland():
    with patch("aura.agents.vision._detect_wayland", return_value=True):
        return AgentVision()


def test_can_handle_screenshot(vision):
    assert vision.can_handle(AgentRequest(text="скриншот"))


def test_can_handle_snimok(vision):
    assert vision.can_handle(AgentRequest(text="сделай снимок"))


def test_can_handle_snimok_ekrana(vision):
    assert vision.can_handle(AgentRequest(text="снимок экрана"))


def test_cannot_handle_time(vision):
    assert not vision.can_handle(AgentRequest(text="который час"))


@pytest.mark.asyncio
async def test_handle_screenshot(vision):
    vision.pyautogui.screenshot.return_value = MagicMock()
    resp = await vision.handle(AgentRequest(text="скриншот"))
    assert resp.status == AgentStatus.OK
    assert "Скриншот" in resp.text
    assert vision.pyautogui.screenshot.called


@pytest.mark.asyncio
async def test_handle_not_ready(vision):
    vision.ready = False
    resp = await vision.handle(AgentRequest(text="скриншот"))
    assert "недоступно" in resp.text.lower() or "Зрение" in resp.text


@pytest.mark.asyncio
async def test_handle_error(vision):
    vision.pyautogui.screenshot.side_effect = Exception("boom")
    resp = await vision.handle(AgentRequest(text="скриншот"))
    assert "Ошибка" in resp.text


@pytest.mark.asyncio
async def test_handle_not_handled(vision):
    resp = await vision.handle(AgentRequest(text="просто болтовня"))
    assert resp.status == AgentStatus.NOT_HANDLED


def test_wayland_flag(vision, vision_wayland):
    assert vision.is_wayland is False
    assert vision_wayland.is_wayland is True
    assert vision_wayland.ready is False
