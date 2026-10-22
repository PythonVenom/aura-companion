"""#149 MultiApp — тесты."""
from __future__ import annotations

import pytest

from aura.agents import multi_app as MA
from aura.agents.multi_app import AgentMultiApp, Step, load_scenarios
from aura.core.protocol import AgentRequest


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(MA, "SCENARIOS_PATH", tmp_path / "scenarios.json")
    yield


@pytest.fixture
def agent():
    return AgentMultiApp()


@pytest.fixture
def req():
    def _make(text: str):
        return AgentRequest(text=text, user="test")
    return _make


@pytest.mark.parametrize("text", [
    "режим работы", "режим кино", "режим отдыха", "уборка",
])
def test_can_handle(agent, req, text):
    assert agent.can_handle(req(text))


def test_cannot_handle_random(agent, req):
    assert not agent.can_handle(req("привет"))


def test_default_scenarios_loaded():
    scenarios = load_scenarios()
    assert len(scenarios) >= 4
    names = [s.name for s in scenarios]
    assert "работа" in names


def test_scenario_has_steps():
    for s in load_scenarios():
        assert len(s.steps) > 0
        for step in s.steps:
            assert step.agent
            assert step.action


@pytest.mark.asyncio
async def test_handle_работа(agent, req):
    resp = await agent.handle(req("режим работы"))
    assert "работа" in resp.text.lower()
    assert "app_launcher" in resp.text


@pytest.mark.asyncio
async def test_handle_кино(agent, req):
    resp = await agent.handle(req("режим кино"))
    assert "кино" in resp.text.lower()


@pytest.mark.asyncio
async def test_handle_list(agent, req):
    resp = await agent.handle(req("сценарий"))
    assert "Сценарии" in resp.text or "работа" in resp.text.lower()


def test_save_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(MA, "SCENARIOS_PATH", tmp_path / "s.json")
    s = MA.Scenario(
        name="тест",
        triggers=["test"],
        steps=[Step("test_agent", "test_action", {"k": "v"})],
    )
    MA.save_scenarios([s])
    loaded = MA.load_scenarios()
    assert loaded[0].name == "тест"
    assert loaded[0].steps[0].agent == "test_agent"


def test_list_scenarios(agent):
    out = agent.list_scenarios()
    assert "работа" in out
    assert "кино" in out
