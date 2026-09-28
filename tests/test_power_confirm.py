"""Confirm для необратимых действий."""
import pytest
from aura.agents.power import AgentPower
from aura.core.protocol import AgentRequest


@pytest.fixture(autouse=True)
def _reset_pending():
    AgentPower._pending = None
    yield
    AgentPower._pending = None


@pytest.mark.asyncio
async def test_shutdown_needs_confirm():
    a = AgentPower()
    r = await a.handle(AgentRequest(text="выключи пк"))
    assert AgentPower._pending == "shutdown"
    assert "да" in r.text.lower() or "нет" in r.text.lower()


@pytest.mark.asyncio
async def test_confirm_executes(monkeypatch):
    a = AgentPower()
    called = []
    monkeypatch.setattr(a, "_shutdown", lambda: called.append(1) or "ok")
    await a.handle(AgentRequest(text="выключи пк"))
    r = await a.handle(AgentRequest(text="да"))
    assert called
    assert AgentPower._pending is None


@pytest.mark.asyncio
async def test_cancel(monkeypatch):
    a = AgentPower()
    called = []
    monkeypatch.setattr(a, "_shutdown", lambda: called.append(1) or "ok")
    await a.handle(AgentRequest(text="выключи пк"))
    r = await a.handle(AgentRequest(text="нет"))
    assert not called
    assert "тмен" in r.text


@pytest.mark.asyncio
async def test_reboot_confirm():
    a = AgentPower()
    await a.handle(AgentRequest(text="перезагрузи"))
    assert AgentPower._pending == "reboot"


@pytest.mark.asyncio
async def test_lock_no_confirm(monkeypatch):
    a = AgentPower()
    monkeypatch.setattr(a, "_lock", lambda: "locked")
    r = await a.handle(AgentRequest(text="заблокируй экран"))
    assert AgentPower._pending is None
    assert "locked" in r.text
