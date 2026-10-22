"""#140 AgentPlanner — тесты."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from aura.agents.planner import AgentPlanner
from aura.core.protocol import AgentRequest


@pytest.fixture
def agent():
    return AgentPlanner()


@pytest.fixture
def req():
    def _make(text: str):
        return AgentRequest(text=text, user="test")
    return _make


@pytest.mark.parametrize("text", [
    "план", "спланируй", "сделай за меня", "автономно",
])
def test_can_handle(agent, req, text):
    assert agent.can_handle(req(text))


def test_cannot_handle_random(agent, req):
    assert not agent.can_handle(req("привет"))


def test_run_plan_ok(agent):
    fake = {"answer": "Готово", "steps": [], "iterations": 1}
    with patch("aura.agents.planner.react_loop", return_value=fake):
        result = agent._run_plan("test")
    assert result["answer"] == "Готово"


def test_run_plan_exception(agent):
    with patch("aura.agents.planner.react_loop", side_effect=RuntimeError("boom")):
        result = agent._run_plan("test")
    assert "❌" in result["answer"]
    assert result["iterations"] == 0


@pytest.mark.asyncio
async def test_handle_returns_answer(agent, req):
    fake = {"answer": "Готово", "steps": [], "iterations": 1}
    with patch("aura.agents.planner.react_loop", return_value=fake):
        resp = await agent.handle(req("спланируй"))
    assert "Готово" in resp.text


@pytest.mark.asyncio
async def test_handle_records_to_recall(agent, req):
    fake = {"answer": "OK", "steps": [], "iterations": 1}
    with patch("aura.agents.planner.react_loop", return_value=fake):
        with patch("aura.agents.planner.record") as mock_rec:
            await agent.handle(req("план"))
    mock_rec.assert_called_once()


@pytest.mark.asyncio
async def test_handle_shows_steps(agent, req):
    fake = {
        "answer": "OK",
        "steps": [
            {"action": "internet", "args": {"query": "рецепт"}},
            {"action": "checklist", "args": {"item": "борщ"}},
        ],
        "iterations": 2,
    }
    with patch("aura.agents.planner.react_loop", return_value=fake):
        resp = await agent.handle(req("план"))
    assert "internet" in resp.text
    assert "checklist" in resp.text
