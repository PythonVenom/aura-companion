"""TDD: VK Web адаптер."""
import pytest
from aura.agents.vk_web import AgentVKWeb
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def agent():
    return AgentVKWeb()


@pytest.mark.parametrize("text", [
    "открой вк",
    "вк музыка",
    "вконтакте друзья",
    "вк группы",
    "вк новости",
    "напиши в вк",
])
def test_can_handle_vk(agent, text):
    assert agent.can_handle(AgentRequest(text=text)) is True


@pytest.mark.parametrize("text", [
    "включи музыку",
    "привет",
    "какие вкладки открыты",  # не VK — это browser_tabs
    "который час",
])
def test_cannot_handle_other(agent, text):
    assert agent.can_handle(AgentRequest(text=text)) is False


@pytest.mark.asyncio
async def test_handle_returns_ok(agent):
    resp = await agent.handle(AgentRequest(text="открой вк"))
    assert resp.status == AgentStatus.OK


@pytest.mark.asyncio
async def test_handle_list_chats_no_bridge(agent):
    """Без bridge — сообщение об ошибке, не падение."""
    from unittest.mock import patch
    with patch("aura.agents.vk_web.send_command", return_value=None):
        resp = await agent.handle(AgentRequest(text="вк сообщения"))
    assert resp.status == AgentStatus.OK
    # Текст начинается с 🌐 VK или 🌐 Ошибка
    assert "🌐" in resp.text
