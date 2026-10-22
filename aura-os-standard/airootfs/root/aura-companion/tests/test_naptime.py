"""#142 AgentNaptime — тесты."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from aura.agents import naptime as N
from aura.agents.naptime import AgentNaptime
from aura.core.protocol import AgentRequest


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(N, "STATE_PATH", tmp_path / "naptime.json")
    yield


@pytest.fixture
def agent():
    return AgentNaptime()


@pytest.fixture
def req():
    def _make(text: str):
        return AgentRequest(text=text, user="test")
    return _make


def test_not_active_default():
    assert N.is_naptime() is False


def test_enable_5min():
    N._enable(5)
    assert N.is_naptime() is True
    assert 4 <= N.remaining_min() <= 5


def test_disable():
    N._enable(5)
    N._disable()
    assert N.is_naptime() is False


def test_expired():
    """Прошедший таймер → False."""
    N._enable(-1)  # в прошлом
    assert N.is_naptime() is False


@pytest.mark.parametrize("text", [
    "не беспокоить", "тихий режим", "не мешай",
    "статус тишины",
])
def test_can_handle(agent, req, text):
    assert agent.can_handle(req(text))


def test_cannot_handle_random(agent, req):
    assert not agent.can_handle(req("привет"))


@pytest.mark.asyncio
async def test_handle_enable_30min(agent, req):
    resp = await agent.handle(req("не беспокоить"))
    assert "30" in resp.text
    assert N.is_naptime() is True


@pytest.mark.asyncio
async def test_handle_enable_1hour(agent, req):
    resp = await agent.handle(req("не беспокоить на 1 час"))
    assert "1 ч" in resp.text


@pytest.mark.asyncio
async def test_handle_disable(agent, req):
    N._enable(60)
    resp = await agent.handle(req("выключи тишину"))
    assert "выключена" in resp.text.lower()
    assert N.is_naptime() is False


@pytest.mark.asyncio
async def test_handle_status_on(agent, req):
    N._enable(60)
    resp = await agent.handle(req("статус тишины"))
    assert "активна" in resp.text.lower()


@pytest.mark.asyncio
async def test_handle_status_off(agent, req):
    resp = await agent.handle(req("статус тишины"))
    assert "выключена" in resp.text.lower()


def test_parse_minutes_default(agent):
    assert agent._parse_minutes("не беспокоить") == 30


def test_parse_minutes_15(agent):
    assert agent._parse_minutes("на 15 минут") == 15


def test_parse_minutes_2h(agent):
    assert agent._parse_minutes("на 2 часа") == 120
