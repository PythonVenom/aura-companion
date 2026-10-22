"""#34 WineLauncher — тесты."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aura.agents.wine_launcher import AgentWineLauncher
from aura.core.protocol import AgentRequest


@pytest.fixture
def agent():
    return AgentWineLauncher()


@pytest.fixture
def req():
    def _make(text: str):
        return AgentRequest(text=text, user="test")
    return _make


# === can_handle ===

def test_can_handle_run(agent, req):
    assert agent.can_handle(req("запусти exe notepad"))


def test_can_handle_kill(agent, req):
    assert agent.can_handle(req("закрой wine"))


def test_can_handle_list(agent, req):
    assert agent.can_handle(req("список exe"))


def test_cannot_handle_random(agent, req):
    assert not agent.can_handle(req("привет как дела"))


# === graceful degradation ===

@pytest.mark.asyncio
async def test_handle_no_wine(agent, req):
    """Если wine нет — сообщение с инструкцией."""
    with patch("aura.agents.wine_launcher.shutil.which", return_value=None):
        resp = await agent.handle(req("запусти exe test"))
    assert "wine не установлен" in resp.text


# === _run ===

@pytest.mark.asyncio
async def test_run_success(agent, req, tmp_path):
    """Нашли exe → wine запущен через Popen."""
    fake_exe = tmp_path / "notepad.exe"
    fake_exe.touch()

    with patch("aura.agents.wine_launcher.shutil.which", return_value="/usr/bin/wine"):
        with patch.object(agent, "_find_exe", return_value=fake_exe):
            with patch("aura.agents.wine_launcher.subprocess.Popen") as mock_popen:
                resp = await agent.handle(req("запусти exe notepad"))
    assert "🚀" in resp.text
    assert "notepad.exe" in resp.text
    mock_popen.assert_called_once()
    args = mock_popen.call_args[0][0]
    assert args[0] == "wine"
    assert str(fake_exe) == args[1]


@pytest.mark.asyncio
async def test_run_not_found(agent, req):
    """Не нашли exe → сообщение об ошибке."""
    with patch("aura.agents.wine_launcher.shutil.which", return_value="/usr/bin/wine"):
        with patch.object(agent, "_find_exe", return_value=None):
            resp = await agent.handle(req("запусти exe nonexistent"))
    assert "❌" in resp.text
    assert "Не нашёл" in resp.text


@pytest.mark.asyncio
async def test_run_popen_exception(agent, req, tmp_path):
    """Popen падает → ошибка, не краш."""
    fake_exe = tmp_path / "x.exe"
    fake_exe.touch()
    with patch("aura.agents.wine_launcher.shutil.which", return_value="/usr/bin/wine"):
        with patch.object(agent, "_find_exe", return_value=fake_exe):
            with patch("aura.agents.wine_launcher.subprocess.Popen", side_effect=OSError("boom")):
                resp = await agent.handle(req("запусти exe x"))
    assert "Ошибка wine" in resp.text


# === _kill ===

@pytest.mark.asyncio
async def test_kill_calls_wineserver(agent, req):
    with patch("aura.agents.wine_launcher.shutil.which", return_value="/usr/bin/wine"):
        with patch("aura.agents.wine_launcher.subprocess.run") as mock_run:
            resp = await agent.handle(req("закрой wine"))
    assert "wine закрыт" in resp.text
    mock_run.assert_called_once()
    assert mock_run.call_args[0][0] == ["wineserver", "-k"]


# === _list ===

@pytest.mark.asyncio
async def test_list_empty(agent, req):
    with patch("aura.agents.wine_launcher.shutil.which", return_value="/usr/bin/wine"):
        with patch.object(agent, "_scan_exes", return_value=[]):
            resp = await agent.handle(req("список exe"))
    assert "не найдено" in resp.text


@pytest.mark.asyncio
async def test_list_some(agent, req, tmp_path):
    exes = [tmp_path / f"game{i}.exe" for i in range(3)]
    for e in exes:
        e.touch()
    with patch("aura.agents.wine_launcher.shutil.which", return_value="/usr/bin/wine"):
        with patch.object(agent, "_scan_exes", return_value=exes):
            resp = await agent.handle(req("список exe"))
    assert "Найдено 3" in resp.text
    assert "game0.exe" in resp.text


# === _find_exe ===

def test_find_exe_exact(agent, tmp_path):
    exe = tmp_path / "notepad.exe"
    exe.touch()
    with patch.object(agent, "_scan_exes", return_value=[exe]):
        assert agent._find_exe("notepad") == exe


def test_find_exe_with_extension(agent, tmp_path):
    exe = tmp_path / "game.exe"
    exe.touch()
    with patch.object(agent, "_scan_exes", return_value=[exe]):
        assert agent._find_exe("game.exe") == exe


def test_find_exe_fuzzy(agent, tmp_path):
    exe = tmp_path / "notepad++.exe"
    exe.touch()
    with patch.object(agent, "_scan_exes", return_value=[exe]):
        # "notepad" должно fuzzy-матчить "notepad++"
        result = agent._find_exe("notepad")
    assert result == exe


def test_find_exe_no_match(agent, tmp_path):
    exe = tmp_path / "notepad.exe"
    exe.touch()
    with patch.object(agent, "_scan_exes", return_value=[exe]):
        assert agent._find_exe("complete_garbage_xyz") is None


def test_find_exe_empty_query(agent):
    with patch.object(agent, "_scan_exes", return_value=[]):
        assert agent._find_exe("") is None


# === _scan_exes ===

def test_scan_exes_respects_limit(agent, tmp_path, monkeypatch):
    """Не более 500 .exe."""
    fake_dir = tmp_path / "Games"
    fake_dir.mkdir()
    for i in range(600):
        (fake_dir / f"g{i}.exe").touch()
    monkeypatch.setattr(agent, "SEARCH_DIRS", [fake_dir])
    result = agent._scan_exes()
    assert len(result) == 500


def test_scan_exes_nonexistent_dirs(agent, tmp_path, monkeypatch):
    """Несуществующие папки не ломают."""
    monkeypatch.setattr(agent, "SEARCH_DIRS", [tmp_path / "does_not_exist"])
    assert agent._scan_exes() == []
