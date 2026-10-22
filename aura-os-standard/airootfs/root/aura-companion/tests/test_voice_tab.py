"""#144 VoiceTab — тесты."""
from __future__ import annotations

import pytest

from aura.cockpit.configurator import VoiceTab


def test_voicetab_exists():
    assert VoiceTab is not None


def test_voices_list():
    assert len(VoiceTab.VOICES) >= 2
    for val, name in VoiceTab.VOICES:
        assert val
        assert name


def test_speeds_list():
    assert 1.0 in VoiceTab.SPEEDS
    assert len(VoiceTab.SPEEDS) >= 4


@pytest.mark.asyncio
async def test_app_starts_with_voice_tab(tmp_path, monkeypatch):
    from aura.core import profile as P
    monkeypatch.setattr(P, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(P, "PROFILE_JSON", tmp_path / "profile.json")

    from aura.cockpit.configurator import ConfiguratorApp
    from textual.widgets import TabPane
    app = ConfiguratorApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        tabs = app.query(TabPane)
        assert len(tabs) == 5  # Профиль, Уведомления, Ключи, Голос, Агенты


@pytest.mark.asyncio
async def test_voice_tab_renders(tmp_path, monkeypatch):
    from aura.core import profile as P
    monkeypatch.setattr(P, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(P, "PROFILE_JSON", tmp_path / "profile.json")

    from aura.cockpit.configurator import ConfiguratorApp
    from textual.widgets import Select
    app = ConfiguratorApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        selects = app.query(Select)
        ids = [s.id for s in selects]
        assert "select-voice" in ids
        assert "select-speed" in ids
