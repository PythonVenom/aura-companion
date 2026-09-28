"""
Тесты для AgentFocusSwitch.

Мок subprocess. Живой wmctrl не трогаем.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.focus_switch import AgentFocusSwitch
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def fs():
    with patch("aura.agents.focus_switch._detect_wayland", return_value=False):
        return AgentFocusSwitch()


@pytest.fixture
def fs_wayland():
    with patch("aura.agents.focus_switch._detect_wayland", return_value=True):
        return AgentFocusSwitch()


def test_can_handle_focus_vk(fs):
    assert fs.can_handle(AgentRequest(text="фокус на вк"))


def test_can_handle_browser(fs):
    assert fs.can_handle(AgentRequest(text="переключись на браузер"))


def test_can_handle_work(fs):
    assert fs.can_handle(AgentRequest(text="рабочее пространство"))


def test_cannot_handle_time(fs):
    assert not fs.can_handle(AgentRequest(text="который час"))


@pytest.mark.asyncio
async def test_handle_focus_found(fs):
    mock = MagicMock()
    mock.return_value = MagicMock(stdout="0x001 0 0 Firefox Mozilla Firefox\\n", returncode=0)
    with patch("aura.agents.focus_switch.subprocess.run", mock):
        with patch("aura.agents.focus_switch.subprocess.Popen"):
            resp = await fs.handle(AgentRequest(text="фокус на firefox"))
    assert resp.status == AgentStatus.OK
    assert "Фокус перенесён" in resp.text


@pytest.mark.asyncio
async def test_handle_focus_not_found(fs):
    mock = MagicMock()
    mock.return_value = MagicMock(stdout="", returncode=0)
    with patch("aura.agents.focus_switch.subprocess.run", mock):
        with patch("aura.agents.focus_switch.subprocess.Popen"):
            resp = await fs.handle(AgentRequest(text="фокус на vlc"))
    assert resp.status == AgentStatus.OK
    assert "не найдено" in resp.text.lower()


@pytest.mark.asyncio
async def test_handle_work_wayland(fs_wayland):
    with patch("aura.agents.focus_switch.subprocess.Popen"):
        with patch("aura.agents.focus_switch.time.sleep"):
            resp = await fs_wayland.handle(AgentRequest(text="рабочее пространство"))
    assert resp.status == AgentStatus.OK
    # Bug 41: _focus_work отключён, текст изменён
    assert "отключён" in resp.text.lower() or "рабочее пространство" in resp.text.lower()


@pytest.mark.asyncio
async def test_handle_not_handled(fs):
    resp = await fs.handle(AgentRequest(text="просто болтовня"))
    assert resp.status == AgentStatus.NOT_HANDLED


def test_wayland_flag(fs, fs_wayland):
    assert fs.is_wayland is False
    assert fs_wayland.is_wayland is True
