"""Bug 22: 'выключи музыку' ≠ 'выключи ПК'."""
import asyncio
import pytest
from aura.agents.power import AgentPower
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture(autouse=True)
def reset_pending():
    AgentPower._pending = None
    yield
    AgentPower._pending = None


@pytest.mark.parametrize("cmd", [
    "выключи музыку", "выключи звук", "выключи свет", "выключи экран",
    "выключи wifi", "выключи bluetooth", "выключи микрофон",
    "выключи подсветку", "выключи уведомления",
])
def test_not_power_for_non_pc_objects(cmd):
    p = AgentPower()
    r = asyncio.run(p.handle(AgentRequest(text=cmd)))
    assert r.status == AgentStatus.NOT_HANDLED, f"{cmd!r} -> {r.status}"


@pytest.mark.parametrize("cmd", [
    "выключи пк", "выключи компьютер", "poweroff", "shutdown",
])
def test_power_asks_confirm_for_pc(cmd):
    p = AgentPower()
    r = asyncio.run(p.handle(AgentRequest(text=cmd)))
    assert r.status == AgentStatus.OK
    assert "да" in r.text.lower() or "нет" in r.text.lower()
