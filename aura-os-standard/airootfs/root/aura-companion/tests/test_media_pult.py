"""Bug 14 ph.4: единый пульт для VLC/VK/MPRIS."""
from unittest.mock import MagicMock
from aura.agents import media_state as ms
from aura.agents.music_local import AgentMusicLocal
from aura.agents.media_pause import AgentMediaPause
from aura.agents.vk_music import AgentVKMusic
from aura.core.protocol import AgentRequest


def _req(t):
    return AgentRequest(text=t)


def setup_function():
    ms.clear()


def test_pult_routes_pause_to_vk_when_vk_active():
    ms.set_active("vk")
    local = AgentMusicLocal()
    local._vlc_playing = lambda: True
    assert local.can_handle(_req("пауза")) is False


def test_pult_routes_pause_to_local_when_local_active():
    ms.set_active("local")
    local = AgentMusicLocal()
    local._vlc_playing = lambda: True
    assert local.can_handle(_req("пауза")) is True


def test_pult_routes_pause_to_media_pause_when_mpris():
    ms.set_active("mpris")
    mp = AgentMediaPause()
    mp.ready = True
    assert mp.can_handle(_req("пауза")) is True


def test_pult_routes_resume_to_vk():
    ms.set_active("vk")
    vk = AgentVKMusic()
    vk.token = "fake"
    assert vk.can_handle(_req("продолжи музыку")) is True


def test_pult_stop_with_vk_active():
    """«стоп музыка» при vk — уходит в media_pause."""
    ms.set_active("vk")
    local = AgentMusicLocal()
    local._vlc_active = lambda: True
    assert local.can_handle(_req("стоп музыка")) is False
