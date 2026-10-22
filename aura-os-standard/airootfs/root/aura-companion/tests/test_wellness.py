"""Блок 7 — тесты AgentWellness."""
from __future__ import annotations

import pytest

from aura.agents.wellness import AgentWellness, Practice, PRACTICES
from aura.core.protocol import AgentRequest


@pytest.fixture
def agent():
    return AgentWellness()


@pytest.fixture
def req():
    def _make(text: str):
        return AgentRequest(text=text, user="test")
    return _make


# === Practice dataclass ===

def test_practice_total_seconds():
    p = Practice(name="test", phases=[("вдох", 4), ("выдох", 6)], cycles=2)
    assert p.total_seconds == 20


def test_practice_default_cycles():
    p = Practice(name="x", phases=[("a", 1)])
    assert p.cycles == 4


# === PRACTICES константы ===

def test_three_practices_defined():
    assert len(PRACTICES) == 3


def test_478_practice():
    p = PRACTICES["4-7-8"]
    assert p.cycles == 4
    assert p.total_seconds == 76  # (4+7+8) * 4


def test_box_practice():
    p = PRACTICES["box"]
    assert p.total_seconds == 64  # (4+4+4+4) * 4


def test_deep_practice():
    p = PRACTICES["deep"]
    assert p.total_seconds == 60  # (4+6) * 6


# === can_handle ===

@pytest.mark.parametrize("text", [
    "стресс", "тревога", "успокой меня", "подышать",
    "не могу уснуть", "дыхание", "box breathing",
])
def test_can_handle(agent, req, text):
    assert agent.can_handle(req(text))


def test_cannot_handle_random(agent, req):
    assert not agent.can_handle(req("привет как дела"))


# === handle ===

@pytest.mark.asyncio
async def test_handle_sleep_gets_478(agent, req):
    resp = await agent.handle(req("не могу уснуть"))
    assert "4-7-8" in resp.text


@pytest.mark.asyncio
async def test_handle_box(agent, req):
    resp = await agent.handle(req("box breathing для фокуса"))
    assert "Box" in resp.text


@pytest.mark.asyncio
async def test_handle_stress_default_478(agent, req):
    resp = await agent.handle(req("у меня стресс"))
    assert "4-7-8" in resp.text


@pytest.mark.asyncio
async def test_handle_deep(agent, req):
    resp = await agent.handle(req("покажи глубокое дыхание"))
    assert "Глубокое" in resp.text


@pytest.mark.asyncio
async def test_handle_format_has_phases(agent, req):
    resp = await agent.handle(req("стресс"))
    assert "вдох" in resp.text
    assert "выдох" in resp.text
    assert "сек" in resp.text


# === list_practices ===

def test_list_practices(agent):
    out = agent.list_practices()
    assert "4-7-8" in out
    assert "Box" in out
    assert "Глубокое" in out
