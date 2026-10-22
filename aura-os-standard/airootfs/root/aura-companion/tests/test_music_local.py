"""Тесты AgentMusicLocal. VLC не трогаем — mock subprocess."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aura.agents.music_local import AgentMusicLocal
from aura.core.protocol import AgentRequest, AgentStatus


def _make(tmp_path, files=None):
    """Агент с временной папкой и файлами."""
    files = files or ["track1.mp3", "track2.mp3", "Ai Mori - My Heart.flac"]
    for f in files:
        (tmp_path / f).write_bytes(b"")
    return AgentMusicLocal(music_dir=tmp_path)


# --- scan ---

def test_scan_finds_files(tmp_path):
    a = _make(tmp_path)
    assert len(a.tracks) == 3


def test_scan_empty_dir(tmp_path):
    a = AgentMusicLocal(music_dir=tmp_path)
    assert a.tracks == []


def test_scan_missing_dir(tmp_path):
    a = AgentMusicLocal(music_dir=tmp_path / "нет")
    assert a.tracks == []


def test_scan_recursive(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "deep.mp3").write_bytes(b"")
    (tmp_path / "top.mp3").write_bytes(b"")
    a = AgentMusicLocal(music_dir=tmp_path)
    assert len(a.tracks) == 2


def test_scan_filters_extensions(tmp_path):
    (tmp_path / "song.mp3").write_bytes(b"")
    (tmp_path / "readme.txt").write_bytes(b"")
    (tmp_path / "image.jpg").write_bytes(b"")
    a = AgentMusicLocal(music_dir=tmp_path)
    assert len(a.tracks) == 1


# --- can_handle ---

def test_can_handle_play(tmp_path):
    """Bug 14 ph.2: local ловит «включи музыку» только при last_active != vk."""
    from aura.agents import media_state
    media_state.set_active("local")
    a = _make(tmp_path)
    assert a.can_handle(AgentRequest(text="включи музыку"))


def test_can_handle_track(tmp_path):
    a = _make(tmp_path)
    assert a.can_handle(AgentRequest(text="включи трек Ai Mori"))


def test_can_handle_list(tmp_path):
    a = _make(tmp_path)
    assert a.can_handle(AgentRequest(text="сколько треков"))


def test_cannot_handle_time(tmp_path):
    a = _make(tmp_path)
    assert not a.can_handle(AgentRequest(text="который час"))


def test_cannot_handle_pause_without_vlc(tmp_path):
    """«пауза» без активного VLC — не наше."""
    a = _make(tmp_path)
    with patch.object(a, "_vlc_playing", return_value=False):
        assert not a.can_handle(AgentRequest(text="пауза"))


# --- handle ---

@pytest.mark.asyncio
async def test_handle_list(tmp_path):
    a = _make(tmp_path)
    resp = await a.handle(AgentRequest(text="сколько треков"))
    assert "3" in resp.text


@pytest.mark.asyncio
async def test_handle_play_random(tmp_path):
    a = _make(tmp_path)
    with patch("aura.agents.music_local.subprocess.Popen") as mp:
        resp = await a.handle(AgentRequest(text="включи музыку"))
    assert "Включила" in resp.text
    mp.assert_called_once()


@pytest.mark.asyncio
async def test_handle_play_by_query_exact(tmp_path):
    a = _make(tmp_path)
    with patch("aura.agents.music_local.subprocess.Popen") as mp:
        resp = await a.handle(AgentRequest(text="включи трек Ai Mori"))
    assert "Ai Mori" in resp.text
    args = mp.call_args[0][0]
    assert "vlc" in args[0]
    assert "Ai Mori" in args[-1]


@pytest.mark.asyncio
async def test_handle_play_by_query_fuzzy(tmp_path):
    a = _make(tmp_path)
    with patch("aura.agents.music_local.subprocess.Popen"):
        resp = await a.handle(AgentRequest(text="включи трек ai mori my"))
    assert "Ai Mori" in resp.text or "не найден" not in resp.text


@pytest.mark.asyncio
async def test_handle_play_by_query_not_found(tmp_path):
    a = _make(tmp_path)
    resp = await a.handle(AgentRequest(text="включи трек zzzzz"))
    assert "не найден" in resp.text.lower()


@pytest.mark.asyncio
async def test_handle_empty_dir(tmp_path):
    a = AgentMusicLocal(music_dir=tmp_path)
    resp = await a.handle(AgentRequest(text="включи музыку"))
    assert "пуста" in resp.text.lower()


# --- playerctl ---

def test_pause_ok(tmp_path):
    a = _make(tmp_path)
    mock = MagicMock(returncode=0, stdout="", stderr="")
    with patch("aura.agents.music_local.get_media",
               side_effect=Exception("PAL disabled")):
        with patch("aura.agents.music_local.subprocess.run", return_value=mock):
            assert "Пауза" in a.pause()


def test_pause_fail(tmp_path):
    a = _make(tmp_path)
    mock = MagicMock(returncode=1, stdout="", stderr="")
    with patch("aura.agents.music_local.get_media",
               side_effect=Exception("PAL disabled")):
        with patch("aura.agents.music_local.subprocess.run", return_value=mock):
            assert "не отвечает" in a.pause()


def test_vlc_active_playing(tmp_path):
    a = _make(tmp_path)
    mock = MagicMock(returncode=0, stdout="Playing\n", stderr="")
    with patch("aura.agents.music_local.subprocess.run", return_value=mock):
        assert a._vlc_active() is True


def test_vlc_active_stopped(tmp_path):
    a = _make(tmp_path)
    mock = MagicMock(returncode=0, stdout="Stopped\n", stderr="")
    with patch("aura.agents.music_local.subprocess.run", return_value=mock):
        assert a._vlc_active() is False


# --- extract query ---

def test_extract_query_track(tmp_path):
    a = _make(tmp_path)
    assert a._extract_query("включи трек Ai Mori") == "Ai Mori"


def test_extract_query_music_empty(tmp_path):
    a = _make(tmp_path)
    assert a._extract_query("включи музыку") == ""


# --- not handled ---

@pytest.mark.asyncio
async def test_handle_not_handled(tmp_path):
    a = _make(tmp_path)
    resp = await a.handle(AgentRequest(text="просто болтовня"))
    assert resp.status == AgentStatus.NOT_HANDLED
