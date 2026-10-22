"""Bug 30 regression — media_state не должен залипать на vk."""
from __future__ import annotations

from pathlib import Path

import pytest

from aura.agents import media_state


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    """Изолированный STATE_PATH."""
    monkeypatch.setattr(media_state, "STATE_PATH", tmp_path / "state.json")
    yield


def test_set_and_get_active():
    media_state.set_active("vk")
    assert media_state.get_active() == "vk"


def test_clear_resets():
    media_state.set_active("vk")
    media_state.clear()
    assert media_state.get_active() is None


def test_invalid_source_ignored():
    media_state.set_active("malware")
    assert media_state.get_active() is None


def test_music_local_stop_clears_state(monkeypatch):
    """Bug 30: music_local.stop() → media_state.clear()."""
    media_state.set_active("vk")
    from aura.agents.music_local import AgentMusicLocal
    a = AgentMusicLocal()
    # Патчим playerctl, чтобы не звать vlc
    monkeypatch.setattr(a, "_playerctl", lambda *args, **kw: "стоп")
    a.stop()
    assert media_state.get_active() is None


@pytest.mark.asyncio
async def test_vk_music_stop_keywords():
    """Bug 30: «выключи вк» → clear media_state."""
    media_state.set_active("vk")
    from aura.agents.vk_music import AgentVKMusic
    from aura.core.protocol import AgentRequest
    a = AgentVKMusic()
    resp = await a.handle(AgentRequest(text="выключи вк", user="test"))
    assert "остановлена" in resp.text.lower() or "VK" in resp.text
    assert media_state.get_active() is None


def test_vk_music_has_stop_keywords():
    """STOP_KEYWORDS присутствуют в vk_music."""
    from aura.agents.vk_music import AgentVKMusic
    assert hasattr(AgentVKMusic, "STOP_KEYWORDS")
    assert "выключи вк" in AgentVKMusic.STOP_KEYWORDS


def test_vk_music_can_handle_stop():
    """«выключи вк» должен обрабатываться vk_music."""
    from aura.agents.vk_music import AgentVKMusic
    from aura.core.protocol import AgentRequest
    a = AgentVKMusic()
    assert a.can_handle(AgentRequest(text="выключи вк", user="test"))
