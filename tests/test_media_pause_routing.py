"""Bug 14 ph.3: «продолжи/пауза» уважает last_active."""

from aura.agents import media_state as ms
from aura.agents.music_local import AgentMusicLocal
from aura.core.protocol import AgentRequest


def _req(text):
    return AgentRequest(text=text)


def setup_function():
    ms.clear()


def test_pause_goes_to_local_when_local_active():
    ms.set_active("local")
    local = AgentMusicLocal()
    local._vlc_playing = lambda: True   # mock
    assert local.can_handle(_req("пауза")) is True


def test_pause_yields_when_vk_active():
    """VK активен → music_local НЕ должен ловить «пауза»."""
    ms.set_active("vk")
    local = AgentMusicLocal()
    local._vlc_playing = lambda: True
    assert local.can_handle(_req("пауза")) is False


def test_resume_yields_when_vk_active():
    ms.set_active("vk")
    local = AgentMusicLocal()
    local._vlc_paused = lambda: True
    assert local.can_handle(_req("продолжи музыку")) is False


def test_resume_goes_to_local_when_local_active():
    ms.set_active("local")
    local = AgentMusicLocal()
    local._vlc_paused = lambda: True
    assert local.can_handle(_req("продолжи музыку")) is True
