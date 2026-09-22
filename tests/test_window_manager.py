"""Тесты для AgentWindowManager."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.window_manager import AgentWindowManager
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def wm():
    """Не Wayland, не KDE — используется wmctrl."""
    with patch("aura.agents.window_manager._detect_wayland", return_value=False), \
         patch("aura.agents.window_manager._detect_kde", return_value=False):
        return AgentWindowManager()


@pytest.fixture
def wm_kde():
    """Не Wayland, KDE с qdbus6."""
    with patch("aura.agents.window_manager._detect_wayland", return_value=False), \
         patch("aura.agents.window_manager._detect_kde", return_value=True), \
         patch("aura.agents.window_manager.shutil.which", return_value="/usr/bin/qdbus6"):
        return AgentWindowManager()


@pytest.fixture
def wm_wayland():
    with patch("aura.agents.window_manager._detect_wayland", return_value=True), \
         patch("aura.agents.window_manager._detect_kde", return_value=False):
        return AgentWindowManager()


def test_can_handle_desktop(wm):
    assert wm.can_handle(AgentRequest(text="следующий рабочий стол"))


def test_can_handle_split(wm):
    assert wm.can_handle(AgentRequest(text="раздели экран"))


def test_cannot_handle_time(wm):
    assert not wm.can_handle(AgentRequest(text="который час"))


@pytest.mark.asyncio
async def test_handle_desktop_next_wmctrl(wm):
    with patch("aura.agents.window_manager.subprocess.run") as mock_run:
        resp = await wm.handle(AgentRequest(text="следующий рабочий стол"))
    assert resp.status == AgentStatus.OK
    assert "следующий" in resp.text.lower()
    mock_run.assert_called()
    assert mock_run.call_args[0][0] == ["wmctrl", "-s", "+1"]


@pytest.mark.asyncio
async def test_handle_desktop_next_kde(wm_kde):
    with patch("aura.agents.window_manager.subprocess.run") as mock_run:
        resp = await wm_kde.handle(AgentRequest(text="следующий рабочий стол"))
    assert resp.status == AgentStatus.OK
    assert "следующий" in resp.text.lower()
    mock_run.assert_called()
    assert mock_run.call_args[0][0] == ["qdbus6", "org.kde.KWin", "/KWin", "nextDesktop"]


@pytest.mark.asyncio
async def test_handle_desktop_prev_kde(wm_kde):
    with patch("aura.agents.window_manager.subprocess.run") as mock_run:
        resp = await wm_kde.handle(AgentRequest(text="предыдущий рабочий стол"))
    assert "предыдущий" in resp.text.lower()
    assert mock_run.call_args[0][0] == ["qdbus6", "org.kde.KWin", "/KWin", "previousDesktop"]


@pytest.mark.asyncio
async def test_handle_desktop_number_kde(wm_kde):
    with patch("aura.agents.window_manager.subprocess.run") as mock_run:
        resp = await wm_kde.handle(AgentRequest(text="рабочий стол номер 2"))
    assert "2" in resp.text
    assert mock_run.call_args[0][0] == ["qdbus6", "org.kde.KWin", "/KWin", "setCurrentDesktop", "2"]


@pytest.mark.asyncio
async def test_handle_desktop_prev_wmctrl(wm):
    with patch("aura.agents.window_manager.subprocess.run") as mock_run:
        resp = await wm.handle(AgentRequest(text="предыдущий рабочий стол"))
    assert "предыдущий" in resp.text.lower()
    assert mock_run.call_args[0][0] == ["wmctrl", "-s", "-1"]


@pytest.mark.asyncio
async def test_handle_desktop_number_wmctrl(wm):
    with patch("aura.agents.window_manager.subprocess.run") as mock_run:
        resp = await wm.handle(AgentRequest(text="рабочий стол номер 3"))
    assert "3" in resp.text
    assert mock_run.call_args[0][0] == ["wmctrl", "-s", "2"]


@pytest.mark.asyncio
async def test_handle_wayland(wm_wayland):
    resp = await wm_wayland.handle(AgentRequest(text="следующий рабочий стол"))
    assert resp.status == AgentStatus.OK
    # Wayland не KDE — команда есть, но реального вызова wmctrl нет


@pytest.mark.asyncio
async def test_handle_not_handled(wm):
    resp = await wm.handle(AgentRequest(text="просто болтовня"))
    assert resp.status == AgentStatus.NOT_HANDLED


def test_focus_window_found(wm):
    mock = MagicMock()
    mock.return_value = MagicMock(stdout="0x001 0 0 host code-oss — VSCode\n", returncode=0)
    with patch("aura.agents.window_manager.subprocess.run", mock):
        result = wm._focus_window("code-oss", "среда")
    assert "Сфокусировалась" in result


def test_focus_window_not_found(wm):
    mock = MagicMock()
    mock.return_value = MagicMock(stdout="", returncode=0)
    with patch("aura.agents.window_manager.subprocess.run", mock):
        with patch("aura.agents.window_manager.subprocess.Popen"):
            result = wm._focus_window("code-oss", "среда")
    assert "не найдено" in result.lower()


def test_kde_flag(wm, wm_kde):
    assert wm.is_kde is False
    assert wm_kde.is_kde is True


def test_wayland_flag(wm, wm_wayland):
    assert wm.is_wayland is False
    assert wm_wayland.is_wayland is True
