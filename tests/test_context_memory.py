"""
Тесты для AgentContextMemory.

Мок subprocess. Живой wmctrl не трогаем.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.context_memory import AgentContextMemory
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def cm():
    with patch("aura.agents.context_memory._detect_wayland", return_value=False):
        return AgentContextMemory()


@pytest.fixture
def cm_wayland():
    with patch("aura.agents.context_memory._detect_wayland", return_value=True):
        return AgentContextMemory()


def test_can_handle_windows(cm):
    assert cm.can_handle(AgentRequest(text="открытые окна"))


def test_can_handle_source(cm):
    assert cm.can_handle(AgentRequest(text="последний источник"))


def test_cannot_handle_time(cm):
    assert not cm.can_handle(AgentRequest(text="который час"))


def test_detect_process_youtube(cm):
    assert cm._detect_process("YouTube — Firefox") == "youtube"


def test_detect_process_vlc(cm):
    assert cm._detect_process("VLC media player") == "vlc"


def test_detect_process_code(cm):
    assert cm._detect_process("Code — main.py") == "code"


def test_detect_process_unknown(cm):
    assert cm._detect_process("Some random window") == "unknown"


def test_scan_windows(cm):
    mock = MagicMock()
    mock.return_value = MagicMock(
        stdout="0x01 0 0 host YouTube — Firefox\n0x02 0 0 host Code — main.py\n",
        returncode=0,
    )
    with patch("aura.agents.context_memory.subprocess.run", mock):
        result = cm.scan_windows()
    assert result is True
    assert len(cm.window_history) == 2
    assert cm.window_history[0]["process"] == "youtube"


def test_scan_windows_wayland(cm_wayland):
    assert cm_wayland.scan_windows() is False


@pytest.mark.asyncio
async def test_handle_windows(cm):
    mock = MagicMock()
    mock.return_value = MagicMock(
        stdout="0x01 0 0 host YouTube — Firefox\n", returncode=0,
    )
    with patch("aura.agents.context_memory.subprocess.run", mock):
        resp = await cm.handle(AgentRequest(text="открытые окна"))
    assert resp.status == AgentStatus.OK
    assert "YouTube" in resp.text


@pytest.mark.asyncio
async def test_handle_source(cm):
    mock = MagicMock()
    mock.return_value = MagicMock(
        stdout="0x01 0 0 host YouTube — Firefox\n", returncode=0,
    )
    with patch("aura.agents.context_memory.subprocess.run", mock):
        resp = await cm.handle(AgentRequest(text="последний источник"))
    assert resp.status == AgentStatus.OK
    assert "YouTube" in resp.text


@pytest.mark.asyncio
async def test_handle_wayland(cm_wayland):
    resp = await cm_wayland.handle(AgentRequest(text="открытые окна"))
    assert "Wayland" in resp.text


@pytest.mark.asyncio
async def test_handle_not_handled(cm):
    resp = await cm.handle(AgentRequest(text="просто болтовня"))
    assert resp.status == AgentStatus.NOT_HANDLED


def test_wayland_flag(cm, cm_wayland):
    assert cm.is_wayland is False
    assert cm_wayland.is_wayland is True
