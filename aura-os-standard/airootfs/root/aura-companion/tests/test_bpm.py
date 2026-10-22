"""BPM метроном (ADR-044)."""
import pytest
from aura.agents.bpm import AgentBPM, bpm_to_interval
from aura.core.protocol import AgentRequest, AgentStatus


def test_interval_120():
    assert bpm_to_interval(120) == 500


def test_interval_60():
    assert bpm_to_interval(60) == 1000


def test_interval_zero_raises():
    with pytest.raises(ValueError):
        bpm_to_interval(0)


def test_interval_too_fast():
    with pytest.raises(ValueError):
        bpm_to_interval(500)


def test_can_handle():
    a = AgentBPM()
    assert a.can_handle(AgentRequest(text="метроном 120")) is True
    assert a.can_handle(AgentRequest(text="привет")) is False


@pytest.mark.asyncio
async def test_handle_allegro():
    a = AgentBPM()
    r = await a.handle(AgentRequest(text="метроном 120"))
    assert r.status == AgentStatus.OK
    assert "500" in r.text
    assert "Allegro" in r.text


@pytest.mark.asyncio
async def test_handle_largo():
    a = AgentBPM()
    r = await a.handle(AgentRequest(text="метроном 50"))
    assert "Largo" in r.text


@pytest.mark.asyncio
async def test_handle_no_bpm():
    a = AgentBPM()
    r = await a.handle(AgentRequest(text="метроном"))
    assert "Скажи" in r.text
