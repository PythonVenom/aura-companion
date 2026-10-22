"""AT-SPI."""
import pytest
from aura.agents.at_spi import AgentAtSpi
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def agent():
    return AgentAtSpi()


@pytest.mark.parametrize("text", ["прочитай экран", "что на экране", "найти кнопку"])
def test_can_handle(agent, text):
    assert agent.can_handle(AgentRequest(text=text)) is True


@pytest.mark.parametrize("text", ["привет", "включи музыку", "который час"])
def test_cannot_handle(agent, text):
    assert agent.can_handle(AgentRequest(text=text)) is False


@pytest.mark.asyncio
async def test_handle_graceful(agent):
    resp = await agent.handle(AgentRequest(text="прочитай экран"))
    assert resp.status == AgentStatus.OK
