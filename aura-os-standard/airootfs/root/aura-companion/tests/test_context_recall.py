"""#141 ContextRecall — тесты."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from aura.agents import context_recall as CR
from aura.agents.context_recall import AgentContextRecall
from aura.core.protocol import AgentRequest


@pytest.fixture
def agent():
    return AgentContextRecall()


@pytest.fixture
def req():
    def _make(text: str):
        return AgentRequest(text=text, user="test")
    return _make


@pytest.mark.parametrize("text", [
    "что я делал", "что было недавно", "последние события",
])
def test_can_handle(agent, req, text):
    assert agent.can_handle(req(text))


def test_cannot_handle_random(agent, req):
    assert not agent.can_handle(req("привет"))


def test_parse_minutes_default(agent):
    assert agent._parse_minutes("что было недавно") == 10


def test_parse_minutes_30(agent):
    assert agent._parse_minutes("что было 30 минут назад") == 30


def test_parse_minutes_2h(agent):
    assert agent._parse_minutes("что было 2 часа назад") == 120


@pytest.mark.asyncio
async def test_handle_returns_recall(agent, req):
    with patch.object(CR, "format_recall", return_value="📋 Журнал"):
        resp = await agent.handle(req("что я делал"))
    assert "Журнал" in resp.text
