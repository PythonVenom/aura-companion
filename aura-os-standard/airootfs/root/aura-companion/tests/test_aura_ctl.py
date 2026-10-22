"""Тесты для scripts/aura_ctl.py — CLI управления Aura."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import aura_ctl


@pytest.fixture
def tmp_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(aura_ctl, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(aura_ctl, "PAUSE_FLAG", tmp_path / "aura_pause.flag")
    monkeypatch.setattr(aura_ctl, "STATUS_FILE", tmp_path / "aura_status.json")
    return tmp_path


@pytest.fixture
def mock_systemctl(monkeypatch):
    calls = []
    def fake_run(cmd, **kw):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="active\n", stderr="")
    monkeypatch.setattr(aura_ctl, "_run", fake_run)
    return calls


@pytest.fixture(autouse=True)
def _silent_notify(monkeypatch):
    monkeypatch.setattr(aura_ctl, "_notify", lambda *a, **k: None)


def test_pause_creates_flag(tmp_cache):
    assert aura_ctl.cmd_pause(None) == 0
    assert (tmp_cache / "aura_pause.flag").exists()


def test_pause_idempotent(tmp_cache):
    aura_ctl.cmd_pause(None)
    assert aura_ctl.cmd_pause(None) == 0
    assert (tmp_cache / "aura_pause.flag").exists()


def test_resume_removes_flag(tmp_cache):
    (tmp_cache / "aura_pause.flag").touch()
    assert aura_ctl.cmd_resume(None) == 0
    assert not (tmp_cache / "aura_pause.flag").exists()


def test_resume_idempotent(tmp_cache):
    assert aura_ctl.cmd_resume(None) == 0
    assert not (tmp_cache / "aura_pause.flag").exists()


def test_restart_calls_systemctl(tmp_cache, mock_systemctl):
    assert aura_ctl.cmd_restart(None) == 0
    assert ["systemctl", "--user", "restart", "aura.service"] in mock_systemctl


def test_kill_calls_systemctl(tmp_cache, mock_systemctl):
    assert aura_ctl.cmd_kill(None) == 0
    assert ["systemctl", "--user", "kill", "-s", "SIGKILL", "aura.service"] in mock_systemctl


def test_status_reads_json(tmp_cache, mock_systemctl):
    (tmp_cache / "aura_status.json").write_text(
        json.dumps({"state": "listening", "text": "test"}), encoding="utf-8"
    )
    args = MagicMock(json=True)
    assert aura_ctl.cmd_status(args) == 0


def test_status_no_file(tmp_cache, mock_systemctl):
    args = MagicMock(json=True)
    assert aura_ctl.cmd_status(args) == 0

def test_panic_stops_service(tmp_cache, mock_systemctl):
    assert aura_ctl.cmd_panic(None) == 0
    assert ["systemctl", "--user", "stop", "aura.service"] in mock_systemctl


def test_panic_mutes_mic(tmp_cache, mock_systemctl):
    assert aura_ctl.cmd_panic(None) == 0
    cmds = [c[0] if isinstance(c, list) else c for c in mock_systemctl]
    assert any("wpctl" in str(c) for c in cmds)


def test_panic_writes_log(tmp_cache, mock_systemctl):
    aura_ctl.cmd_panic(None)
    log = tmp_cache / "panic.log"
    assert log.exists()
    assert "panic" in log.read_text(encoding="utf-8").lower()


def test_mute_mic(tmp_cache, mock_systemctl):
    assert aura_ctl.cmd_mute(None) == 0
    assert any("set-mute" in str(c) and "1" in str(c) for c in mock_systemctl)


def test_unmute_mic(tmp_cache, mock_systemctl):
    assert aura_ctl.cmd_unmute(None) == 0
    assert any("set-mute" in str(c) and "0" in str(c) for c in mock_systemctl)
