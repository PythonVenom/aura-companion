"""Тесты для AgentMediaPause. subprocess — mock, живой звук НЕ трогаем.

Логика: pause() паузит ТОЛЬКО играющих, запоминает кого.
resume() возобновляет ТОЛЬКО запомненных. Иначе двойной звук.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.media_pause import AgentMediaPause
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def agent():
    with patch("aura.agents.media_pause.shutil.which", return_value="/usr/bin/playerctl"):
        return AgentMediaPause()


def _subprocess_fake(players_status: dict[str, str]):
    """players_status = {"firefox.instance_1_62": "Playing", "vlc": "Playing"}.
    Возвращает fake subprocess.run, отвечающий по args.
    """
    def fake_run(cmd, **kw):
        m = MagicMock()
        m.returncode = 0
        m.stdout = ""
        # playerctl --list-all → список имён
        if cmd[:2] == ["playerctl", "--list-all"]:
            m.stdout = "\n".join(players_status.keys()) + "\n"
            return m
        # playerctl -p NAME status
        if len(cmd) >= 4 and cmd[1] == "-p" and cmd[3] == "status":
            name = cmd[2]
            m.stdout = players_status.get(name, "Stopped") + "\n"
            return m
        # playerctl -p NAME pause|play
        if len(cmd) >= 4 and cmd[1] == "-p":
            return m
        return m
    return fake_run


# --- ready ---

def test_ready_when_playerctl_exists():
    with patch("aura.agents.media_pause.shutil.which", return_value="/usr/bin/playerctl"):
        a = AgentMediaPause()
    assert a.ready is True


def test_not_ready_without_playerctl():
    with patch("aura.agents.media_pause.shutil.which", return_value=None):
        a = AgentMediaPause()
    assert a.ready is False


# --- can_handle ---

def test_can_handle_pause(agent):
    assert agent.can_handle(AgentRequest(text="поставь на паузу"))


def test_can_handle_resume(agent):
    assert agent.can_handle(AgentRequest(text="продолжи музыку"))


def test_cannot_handle_time(agent):
    assert not agent.can_handle(AgentRequest(text="который час"))


# --- _list_players / _player_status ---

def test_list_players(agent):
    fake = _subprocess_fake({"firefox.instance_1_62": "Playing", "vlc": "Playing"})
    with patch("aura.agents.media_pause.subprocess.run", side_effect=fake):
        assert agent._list_players() == ["firefox.instance_1_62", "vlc"]


def test_player_status_playing(agent):
    fake = _subprocess_fake({"vlc": "Playing"})
    with patch("aura.agents.media_pause.subprocess.run", side_effect=fake):
        assert agent._player_status("vlc") == "Playing"


def test_player_status_stopped(agent):
    fake = _subprocess_fake({"vlc": "Stopped"})
    with patch("aura.agents.media_pause.subprocess.run", side_effect=fake):
        assert agent._player_status("vlc") == "Stopped"


def test_player_status_no_player(agent):
    fake = _subprocess_fake({})
    with patch("aura.agents.media_pause.subprocess.run", side_effect=fake):
        assert agent._player_status("vlc") == "Stopped"


# --- pause: только играющие ---

def test_pause_only_playing(agent):
    """VLC Playing, Firefox Stopped → паузим только VLC."""
    fake = _subprocess_fake({"firefox.instance_1_62": "Stopped", "vlc": "Playing"})
    with patch("aura.agents.media_pause.subprocess.run", side_effect=fake):
        assert agent.pause() is True
    assert agent._paused_players == ["vlc"]


def test_pause_two_playing(agent):
    """Оба Playing → паузим оба."""
    fake = _subprocess_fake({"firefox.instance_1_62": "Playing", "vlc": "Playing"})
    with patch("aura.agents.media_pause.subprocess.run", side_effect=fake):
        assert agent.pause() is True
    assert set(agent._paused_players) == {"firefox.instance_1_62", "vlc"}


def test_pause_nobody_playing(agent):
    """Никто не играет → return False, список пуст."""
    fake = _subprocess_fake({"firefox.instance_1_62": "Stopped", "vlc": "Paused"})
    with patch("aura.agents.media_pause.subprocess.run", side_effect=fake):
        assert agent.pause() is False
    assert agent._paused_players == []


def test_pause_no_playerctl():
    with patch("aura.agents.media_pause.shutil.which", return_value=None):
        a = AgentMediaPause()
    assert a.pause() is False


def test_pause_swallows_exception(agent):
    with patch("aura.agents.media_pause.subprocess.run", side_effect=OSError("boom")):
        assert agent.pause() is False


# --- resume: только тех, кого паузили ---

def test_resume_only_paused(agent):
    """Сначала паузим VLC, потом resume — только VLC."""
    fake = _subprocess_fake({"firefox.instance_1_62": "Stopped", "vlc": "Playing"})
    calls = []

    def tracking_fake(cmd, **kw):
        calls.append(cmd)
        return fake(cmd, **kw)

    with patch("aura.agents.media_pause.subprocess.run", side_effect=tracking_fake):
        agent.pause()
        calls.clear()
        assert agent.resume() is True

    # Должен быть вызов play только для vlc
    play_cmds = [c for c in calls if c[-1] == "play"]
    assert play_cmds == [["playerctl", "-p", "vlc", "play"]]


def test_resume_without_pause(agent):
    """Не мы паузили — resume ничего не делает."""
    assert agent.resume() is False


def test_resume_no_playerctl():
    with patch("aura.agents.media_pause.shutil.which", return_value=None):
        a = AgentMediaPause()
    assert a.resume() is False


def test_resume_clears_list(agent):
    fake = _subprocess_fake({"vlc": "Playing"})
    with patch("aura.agents.media_pause.subprocess.run", side_effect=fake):
        agent.pause()
        agent.resume()
    assert agent._paused_players == []


# --- handle ---

@pytest.mark.asyncio
async def test_handle_pause(agent):
    fake = _subprocess_fake({"vlc": "Playing"})
    with patch("aura.agents.media_pause.subprocess.run", side_effect=fake):
        resp = await agent.handle(AgentRequest(text="поставь на паузу"))
    assert resp.status == AgentStatus.OK
    assert "пауз" in resp.text.lower()


@pytest.mark.asyncio
async def test_handle_resume(agent):
    fake = _subprocess_fake({"vlc": "Playing"})
    with patch("aura.agents.media_pause.subprocess.run", side_effect=fake):
        agent.pause()
        resp = await agent.handle(AgentRequest(text="продолжи музыку"))
    assert "продолж" in resp.text.lower()


@pytest.mark.asyncio
async def test_handle_not_handled(agent):
    resp = await agent.handle(AgentRequest(text="просто болтовня"))
    assert resp.status == AgentStatus.NOT_HANDLED


# --- specific player ---

def test_specific_player_pause():
    """Если player задан — не сканируем всех, работаем с одним."""
    with patch("aura.agents.media_pause.shutil.which", return_value="/usr/bin/playerctl"):
        agent = AgentMediaPause(player="vlc")
    fake = _subprocess_fake({"vlc": "Playing"})

    with patch("aura.agents.media_pause.subprocess.run", side_effect=fake):
        assert agent.pause() is True
    assert agent._paused_players == ["vlc"]
