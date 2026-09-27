"""Bug 14 ph.2: «включи музыку» идёт в последний активный плеер."""

from aura.agents import media_state as ms
from aura.agents.music_local import AgentMusicLocal
from aura.agents.vk_music import AgentVKMusic
from aura.core.protocol import AgentRequest


def _req(text):
    return AgentRequest(text=text)


def setup_function():
    ms.clear()


def test_vk_active_routes_to_vk(monkeypatch):
    """last_active=vk → vk_music берёт, music_local уступает."""
    ms.set_active("vk")
    local = AgentMusicLocal()
    vk = AgentVKMusic()
    vk.token = "fake"

    assert vk.can_handle(_req("включи музыку")) is True
    assert local.can_handle(_req("включи музыку")) is False


def test_local_active_routes_to_local(monkeypatch):
    """last_active=local → music_local берёт, vk_music уступает."""
    ms.set_active("local")
    local = AgentMusicLocal()
    vk = AgentVKMusic()
    vk.token = "fake"

    assert vk.can_handle(_req("включи музыку")) is False
    assert local.can_handle(_req("включи музыку")) is True


def test_no_last_active_defaults_local():
    """Нет памяти → local (default, работает из коробки)."""
    ms.clear()
    local = AgentMusicLocal()
    vk = AgentVKMusic()
    vk.token = "fake"

    assert vk.can_handle(_req("включи музыку")) is False
    assert local.can_handle(_req("включи музыку")) is True


def test_explicit_vk_always_wins():
    """«включи вк» — явно VK, даже при last_active=local."""
    ms.set_active("local")
    vk = AgentVKMusic()
    vk.token = "fake"

    assert vk.can_handle(_req("включи вк музыку")) is True
