"""
Тесты для AgentMusicDucker.

Мок subprocess.run. Живой pactl не трогаем.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.music_ducker import AgentMusicDucker
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def ducker():
    return AgentMusicDucker()


def _mock_run_with_sink_inputs(*args, **kwargs):
    """Мок pactl: sink-inputs list, get-volume."""
    cmd = args[0] if args else kwargs.get("args", [])
    m = MagicMock()
    if "list" in cmd and "sink-inputs" in cmd:
        m.stdout = "1156\\t58\\t85\\tPipeWire\\n1885\\t58\\t85\\tPipeWire\\n"
    elif "get-sink-input-volume" in cmd:
        m.stdout = "Volume: front-left: 65536 / 85% / 0,00 dB\\n"
    else:
        m.stdout = ""
    m.returncode = 0
    return m


def test_can_handle_duck(ducker):
    assert ducker.can_handle(AgentRequest(text="приглуши музыку"))


def test_can_handle_un_duck(ducker):
    assert ducker.can_handle(AgentRequest(text="восстанови звук"))


def test_cannot_handle_time(ducker):
    assert not ducker.can_handle(AgentRequest(text="который час"))


@pytest.mark.asyncio
async def test_handle_duck(ducker):
    with patch("aura.agents.music_ducker.subprocess.run",
               side_effect=_mock_run_with_sink_inputs):
        resp = await ducker.handle(AgentRequest(text="приглуши музыку"))
    assert resp.status == AgentStatus.OK
    assert "Приглушила" in resp.text
    assert ducker.active_sink_inputs


@pytest.mark.asyncio
async def test_handle_duck_empty(ducker):
    mock = MagicMock()
    mock.return_value = MagicMock(stdout="", returncode=0)
    with patch("aura.agents.music_ducker.subprocess.run", mock):
        resp = await ducker.handle(AgentRequest(text="приглуши музыку"))
    assert resp.status == AgentStatus.OK
    assert "Нет активного" in resp.text


@pytest.mark.asyncio
async def test_handle_un_duck_no_saved(ducker):
    resp = await ducker.handle(AgentRequest(text="восстанови звук"))
    assert resp.status == AgentStatus.OK
    assert "Нет сохранённых" in resp.text


@pytest.mark.asyncio
async def test_handle_not_handled(ducker):
    resp = await ducker.handle(AgentRequest(text="просто болтовня"))
    assert resp.status == AgentStatus.NOT_HANDLED


def test_duck_un_duck_cycle(ducker):
    with patch("aura.agents.music_ducker.subprocess.run",
               side_effect=_mock_run_with_sink_inputs):
        result1 = ducker.duck()
        assert "Приглушила" in result1
        assert len(ducker.active_sink_inputs) == 2

        result2 = ducker.un_duck()
        assert "Восстановила" in result2
        assert ducker.active_sink_inputs == {}


def test_get_volume_failure(ducker):
    with patch("aura.agents.music_ducker.subprocess.run",
               side_effect=Exception("boom")):
        assert ducker._get_sink_input_volume("test") == 100
