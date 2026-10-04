"""Bug 17: ASR-устойчивость power (fuzzy_match adaptive)."""
import pytest
from aura.agents.power import AgentPower
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture(autouse=True)
def _reset_pending():
    AgentPower._pending = None
    yield
    AgentPower._pending = None


def _req(text):
    return AgentRequest(text=text)


@pytest.mark.asyncio
async def test_shutdown_asr_typo():
    """ASR: "выключит" вместо "выключи" (1 правка)."""
    a = AgentPower()
    await a.handle(_req("выключит пк"))
    assert AgentPower._pending == "shutdown"


@pytest.mark.asyncio
async def test_reboot_asr_typo():
    """ASR: "перезагружу" вместо "перезагрузи" (2 правки, длинное слово)."""
    a = AgentPower()
    await a.handle(_req("перезагружу компьютер"))
    assert AgentPower._pending == "reboot"


@pytest.mark.asyncio
async def test_lock_asr_typo(monkeypatch):
    """ASR: "заблокирует" вместо "заблокируй" (2 правки).
    Bug 18: _lock замокан, иначе реальный loginctl заблокирует экран."""
    a = AgentPower()
    called = []
    monkeypatch.setattr(a, "_lock", lambda: called.append(1) or "locked")
    await a.handle(_req("заблокирует экран"))
    assert called, "fuzzy не сработал: _lock не вызван"
    assert AgentPower._pending is None


@pytest.mark.asyncio
async def test_unrelated_still_not_handled():
    a = AgentPower()
    r = await a.handle(_req("привет мир"))
    assert r.status == AgentStatus.NOT_HANDLED


def test_can_handle_asr():
    a = AgentPower()
    assert a.can_handle(_req("выключит пк")) is True
    assert a.can_handle(_req("перезагружу")) is True
    assert a.can_handle(_req("заблокирует")) is True


def test_can_handle_negative():
    a = AgentPower()
    assert a.can_handle(_req("привет мир")) is False
    assert a.can_handle(_req("погода в москве")) is False
