"""ConstructionCalc (ADR-044)."""
import pytest
from aura.agents.construction import AgentConstruction, calc_material, NORMS
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def agent():
    return AgentConstruction()


def _req(t):
    return AgentRequest(text=t)


def test_norms_not_empty():
    assert len(NORMS) >= 10


def test_calc_tile():
    r = calc_material("плитка", 29.0)
    assert r is not None
    assert r.amount == pytest.approx(31.9, abs=0.1)


def test_calc_unknown():
    assert calc_material("несуществующее", 10) is None


def test_can_handle():
    a = AgentConstruction()
    assert a.can_handle(_req("сколько плитки на 29 м²")) is True
    assert a.can_handle(_req("погода")) is False


@pytest.mark.asyncio
async def test_handle_tile(agent):
    r = await agent.handle(_req("сколько плитки на 29 м²"))
    assert r.status == AgentStatus.OK
    assert "плитка" in r.text.lower()
    assert "31" in r.text


@pytest.mark.asyncio
async def test_handle_list(agent):
    r = await agent.handle(_req("какие материалы знаешь"))
    assert "плитка" in r.text.lower()


@pytest.mark.asyncio
async def test_handle_no_area(agent):
    r = await agent.handle(_req("сколько плитки"))
    assert "Скажи" in r.text
