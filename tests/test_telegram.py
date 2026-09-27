"""Telegram Web адаптер (TDD)."""
import pytest
from aura.agents.telegram import AgentTelegram
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def agent():
    return AgentTelegram()


@pytest.mark.parametrize("text", [
    "открой телеграм",
    "телега чаты",
    "тг сообщения",
    "напиши в телеграм",
    "telegram",
])
def test_can_handle_tg(agent, text):
    assert agent.can_handle(AgentRequest(text=text)) is True


@pytest.mark.parametrize("text", [
    "привет",
    "включи музыку",
    "какие вкладки открыты",
    "который час",
])
def test_cannot_handle_other(agent, text):
    assert agent.can_handle(AgentRequest(text=text)) is False


@pytest.mark.asyncio
async def test_handle_open_tg(agent):
    resp = await agent.handle(AgentRequest(text="открой телеграм"))
    assert resp.status == AgentStatus.OK


@pytest.mark.asyncio
async def test_handle_chats_no_bridge(agent):
    from unittest.mock import patch
    with patch("aura.agents.telegram.send_command", return_value=None):
        resp = await agent.handle(AgentRequest(text="телеграм чаты"))
    assert resp.status == AgentStatus.OK
    assert "🌐" in resp.text
