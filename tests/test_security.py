"""#98 Security Agent — тесты."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.security import AgentSecurity
from aura.core.protocol import AgentRequest


@pytest.fixture
def agent():
    return AgentSecurity()


@pytest.fixture
def req():
    def _make(text: str):
        return AgentRequest(text=text, user="test")
    return _make


# === can_handle ===

def test_can_handle_processes(agent, req):
    assert agent.can_handle(req("проверь процессы"))


def test_can_handle_ports(agent, req):
    assert agent.can_handle(req("открытые порты"))


def test_can_handle_viruses(agent, req):
    assert agent.can_handle(req("есть ли вирусы"))


def test_can_handle_integrity(agent, req):
    assert agent.can_handle(req("проверь целостность"))


def test_can_handle_full_report(agent, req):
    assert agent.can_handle(req("полный отчёт безопасности"))


def test_cannot_handle_random(agent, req):
    assert not agent.can_handle(req("привет как дела"))


# === scan_processes ===

def test_scan_processes_clean(agent):
    with patch("aura.agents.security.subprocess.run") as mock:
        mock.return_value = MagicMock(stdout="user 1 0.0 bash\nuser 2 0.0 firefox\n")
        result = agent.scan_processes()
    assert "чиста" in result


def test_scan_processes_suspicious(agent):
    with patch("aura.agents.security.subprocess.run") as mock:
        mock.return_value = MagicMock(stdout="user 1 0.0 nmap -sS 10.0.0.1\n")
        with patch("aura.agents.security.notify") as mock_notify:
            result = agent.scan_processes()
    assert "🚨" in result
    mock_notify.assert_called_once()


def test_scan_processes_handles_exception(agent):
    with patch("aura.agents.security.subprocess.run", side_effect=OSError("boom")):
        result = agent.scan_processes()
    assert "Ошибка" in result


# === check_ports ===

def test_check_ports_listening(agent):
    with patch("aura.agents.security.subprocess.run") as mock:
        mock.return_value = MagicMock(
            stdout="tcp LISTEN 0 128 0.0.0.0:22 0.0.0.0:*\n"
        )
        result = agent.check_ports()
    assert "22" in result


def test_check_ports_empty(agent):
    with patch("aura.agents.security.subprocess.run") as mock:
        mock.return_value = MagicMock(stdout="")
        result = agent.check_ports()
    assert "нет" in result


# === scan_viruses ===

def test_scan_viruses_no_clamav(agent):
    with patch("aura.agents.security.shutil.which", return_value=None):
        result = agent.scan_viruses()
    assert "ClamAV не установлен" in result


def test_scan_viruses_clean(agent, tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "SCAN_PATHS", [tmp_path])
    with patch("aura.agents.security.shutil.which", return_value="/usr/bin/clamscan"):
        with patch("aura.agents.security.subprocess.run") as mock:
            mock.return_value = MagicMock(stdout="", returncode=0)
            result = agent.scan_viruses()
    assert "не найдено" in result


def test_scan_viruses_found(agent, tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "SCAN_PATHS", [tmp_path])
    with patch("aura.agents.security.shutil.which", return_value="/usr/bin/clamscan"):
        with patch("aura.agents.security.subprocess.run") as mock:
            mock.return_value = MagicMock(
                stdout=f"{tmp_path}/bad.exe: Win.Trojan FOUND\n",
            )
            with patch("aura.agents.security.notify") as mock_notify:
                result = agent.scan_viruses()
    assert "🚨" in result
    mock_notify.assert_called_once()


def test_scan_viruses_timeout(agent, tmp_path, monkeypatch):
    import subprocess as sp
    monkeypatch.setattr(agent, "SCAN_PATHS", [tmp_path])
    with patch("aura.agents.security.shutil.which", return_value="/usr/bin/clamscan"):
        with patch("aura.agents.security.subprocess.run", side_effect=sp.TimeoutExpired("clamscan", 120)):
            result = agent.scan_viruses()
    assert "120" in result


# === check_integrity ===

def test_check_integrity_no_auditctl(agent):
    with patch("aura.agents.security.shutil.which", return_value=None):
        result = agent.check_integrity()
    assert "auditd не установлен" in result


def test_check_integrity_with_rules(agent):
    with patch("aura.agents.security.shutil.which", return_value="/usr/bin/auditctl"):
        with patch("aura.agents.security.subprocess.run") as mock:
            mock.return_value = MagicMock(stdout="-w /etc/passwd -p wa\n-a exit,always\n")
            result = agent.check_integrity()
    assert "2 правил" in result


def test_check_integrity_no_rules(agent):
    with patch("aura.agents.security.shutil.which", return_value="/usr/bin/auditctl"):
        with patch("aura.agents.security.subprocess.run") as mock:
            mock.return_value = MagicMock(stdout="")
            result = agent.check_integrity()
    assert "не заданы" in result


# === full_report ===

def test_full_report_signs_and_notifies(agent):
    with patch.object(agent, "scan_processes", return_value="✅ OK"):
        with patch.object(agent, "check_ports", return_value="🔒 нет"):
            with patch.object(agent, "scan_viruses", return_value="✅ чисто"):
                with patch.object(agent, "check_integrity", return_value="🔍 5 правил"):
                    with patch("aura.agents.security.ledger_sign") as mock_sign:
                        mock_sign.return_value = b"\xab" * 64
                        with patch("aura.agents.security.notify") as mock_notify:
                            result = agent.full_report()
    assert "ПОЛНЫЙ ОТЧЁТ" in result
    assert "Подпись:" in result
    mock_sign.assert_called_once()
    mock_notify.assert_called_once()


# === handle (роутинг) ===

@pytest.mark.asyncio
async def test_handle_routes_to_viruses(agent, req):
    with patch.object(agent, "scan_viruses", return_value="✅"):
        resp = await agent.handle(req("есть ли вирусы"))
    assert resp.text == "✅"


@pytest.mark.asyncio
async def test_handle_routes_to_full_report(agent, req):
    with patch.object(agent, "full_report", return_value="🛡️ отчёт"):
        resp = await agent.handle(req("полный отчёт безопасности"))
    assert resp.text == "🛡️ отчёт"


@pytest.mark.asyncio
async def test_handle_default_processes(agent, req):
    with patch.object(agent, "scan_processes", return_value="✅ чисто"):
        resp = await agent.handle(req("проверь систему"))
    assert resp.text == "✅ чисто"
