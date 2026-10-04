"""
Тесты для AgentSecurity.

Мок subprocess.run. Живой ps/ss не запускаем.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.security import AgentSecurity
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def sec():
    return AgentSecurity()


def _mock_run(stdout):
    m = MagicMock()
    m.return_value = MagicMock(stdout=stdout, returncode=0)
    return m


def test_can_handle_ports(sec):
    assert sec.can_handle(AgentRequest(text="проверь порты"))


def test_can_handle_processes(sec):
    assert sec.can_handle(AgentRequest(text="проверь систему"))


def test_cannot_handle_time(sec):
    assert not sec.can_handle(AgentRequest(text="который час"))


@pytest.mark.asyncio
async def test_handle_ports_clean(sec):
    with patch("aura.agents.security.subprocess.run",
               _mock_run("State  Recv-Q Send-Q  Local Address:Port\n")):
        resp = await sec.handle(AgentRequest(text="проверь порты"))
    assert resp.status == AgentStatus.OK
    assert "портов нет" in resp.text.lower()


@pytest.mark.asyncio
async def test_handle_ports_found(sec):
    with patch("aura.agents.security.subprocess.run",
               _mock_run("LISTEN 0 128 0.0.0.0:22 0.0.0.0:*\n")):
        resp = await sec.handle(AgentRequest(text="проверь порты"))
    assert "22" in resp.text


@pytest.mark.asyncio
async def test_handle_processes_clean(sec):
    with patch("aura.agents.security.subprocess.run",
               _mock_run("USER PID COMMAND\nroot 1 init\n")):
        resp = await sec.handle(AgentRequest(text="проверь систему"))
    assert "чиста" in resp.text.lower()


@pytest.mark.asyncio
async def test_handle_processes_suspicious(sec):
    with patch("aura.agents.security.subprocess.run",
               _mock_run("root 999 nmap -sS 192.168.1.1\n")):
        resp = await sec.handle(AgentRequest(text="проверь систему"))
    assert "Подозрительные" in resp.text


@pytest.mark.asyncio
async def test_handle_error(sec):
    with patch("aura.agents.security.subprocess.run",
               side_effect=Exception("boom")):
        resp = await sec.handle(AgentRequest(text="проверь систему"))
    assert resp.status == AgentStatus.OK
    assert "Ошибка" in resp.text


def test_scan_processes_direct(sec):
    with patch("aura.agents.security.subprocess.run",
               _mock_run("")):
        assert "чиста" in sec.scan_processes().lower()
