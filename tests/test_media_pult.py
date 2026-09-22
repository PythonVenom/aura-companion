"""
Тесты для AgentMediaPult.

Мок subprocess. Живой playerctl/firefox не трогаем.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.media_pult import AgentMediaPult
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def mp():
    return AgentMediaPult()


def test_can_handle_youtube(mp):
    assert mp.can_handle(AgentRequest(text="включи ютуб"))


def test_can_handle_stop(mp):
    assert mp.can_handle(AgentRequest(text="стоп медиа"))


def test_can_handle_continue(mp):
    assert mp.can_handle(AgentRequest(text="продолжи медиа"))


def test_cannot_handle_time(mp):
    assert not mp.can_handle(AgentRequest(text="который час"))


def test_play_youtube_default(mp):
    with patch("aura.agents.media_pult.subprocess.Popen") as mock:
        result = mp.play_youtube("dQw4w9WgXcQ")
    assert "YouTube" in result
    assert mock.called


def test_play_youtube_error(mp):
    with patch("aura.agents.media_pult.subprocess.Popen", side_effect=Exception("boom")):
        result = mp.play_youtube("x")
    assert "Не удалось" in result


def test_stop_media(mp):
    with patch("aura.agents.media_pult.subprocess.run") as mock:
        result = mp.stop_media()
    assert "остановлены" in result
    assert mock.called


def test_continue_media(mp):
    with patch("aura.agents.media_pult.subprocess.run") as mock:
        result = mp.continue_media()
    assert "продолжено" in result
    assert mock.called


@pytest.mark.asyncio
async def test_handle_youtube(mp):
    with patch("aura.agents.media_pult.subprocess.Popen"):
        resp = await mp.handle(AgentRequest(text="включи ютуб"))
    assert resp.status == AgentStatus.OK
    assert "YouTube" in resp.text


@pytest.mark.asyncio
async def test_handle_stop(mp):
    with patch("aura.agents.media_pult.subprocess.run"):
        resp = await mp.handle(AgentRequest(text="стоп медиа"))
    assert resp.status == AgentStatus.OK
    assert "остановлены" in resp.text


@pytest.mark.asyncio
async def test_handle_not_handled(mp):
    resp = await mp.handle(AgentRequest(text="просто болтовня"))
    assert resp.status == AgentStatus.NOT_HANDLED


def test_extract_video_id(mp):
    assert mp._extract_video_id("включи ютуб abc123") == "abc123"


def test_extract_video_id_empty(mp):
    assert mp._extract_video_id("включи ютуб") == "dQw4w9WgXcQ"
