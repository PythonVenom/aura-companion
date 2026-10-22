"""
Тесты для AgentParallelUniverse.

Мок subprocess, wmctrl. Живой не трогаем.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.parallel_universe import AgentParallelUniverse
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def pu():
    with patch("aura.agents.parallel_universe._detect_wayland", return_value=False):
        return AgentParallelUniverse()


@pytest.fixture
def pu_wayland():
    with patch("aura.agents.parallel_universe._detect_wayland", return_value=True):
        return AgentParallelUniverse()


def test_can_handle_what_is_background(pu):
    assert pu.can_handle(AgentRequest(text="что в фоне"))


def test_can_handle_start(pu):
    assert pu.can_handle(AgentRequest(text="запусти мультивселенную"))


def test_can_handle_stop(pu):
    assert pu.can_handle(AgentRequest(text="останови мультивселенную"))


def test_cannot_handle_time(pu):
    assert not pu.can_handle(AgentRequest(text="который час"))


def test_start_and_stop(pu):
    with patch.object(pu, "_monitor"):
        result = pu.start()
    assert "запущена" in result
    assert pu.running is True
    result = pu.stop()
    assert "остановлена" in result
    assert pu.running is False


def test_start_wayland(pu_wayland):
    result = pu_wayland.start()
    assert "Недоступно в Wayland" in result


def test_analyze_tabs_found_youtube(pu):
    mock = MagicMock()
    mock.return_value = MagicMock(stdout="0x01 0 0 host YouTube — Firefox\\n", returncode=0)
    with patch("aura.agents.parallel_universe.subprocess.run", mock):
        result = pu._analyze_tabs()
    assert "youtube" in result.lower() or "В фоне" in result


def test_analyze_tabs_empty(pu):
    mock = MagicMock()
    mock.return_value = MagicMock(stdout="", returncode=0)
    with patch("aura.agents.parallel_universe.subprocess.run", mock):
        result = pu._analyze_tabs()
    assert "не найдено" in result.lower()


def test_analyze_error(pu):
    with patch("aura.agents.parallel_universe.subprocess.run", side_effect=Exception("boom")):
        result = pu._analyze_tabs()
    assert "не смогла" in result.lower() or "⚠️" in result


@pytest.mark.asyncio
async def test_handle_insight(pu):
    mock = MagicMock()
    mock.return_value = MagicMock(stdout="", returncode=0)
    with patch("aura.agents.parallel_universe.subprocess.run", mock):
        resp = await pu.handle(AgentRequest(text="что в фоне"))
    assert resp.status == AgentStatus.OK


@pytest.mark.asyncio
async def test_handle_not_handled(pu):
    resp = await pu.handle(AgentRequest(text="просто болтовня"))
    assert resp.status == AgentStatus.NOT_HANDLED
