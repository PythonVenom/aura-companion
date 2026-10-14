"""#143 AgentRules — тесты."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aura.agents import rules as A
from aura.core import rules as R
from aura.agents.rules import AgentRules
from aura.core.protocol import AgentRequest


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "RULES_PATH", tmp_path / "rules.json")
    yield


@pytest.fixture
def agent():
    return AgentRules()


@pytest.fixture
def req():
    def _make(text: str):
        return AgentRequest(text=text, user="test")
    return _make


def test_load_empty():
    assert R.load() == []


def test_add_rule():
    r = R.add("тест", "sunrise", {"agent": "scenes", "cmd": "утро"})
    assert r.name == "тест"
    assert len(R.load()) == 1


def test_add_duplicate_replaces():
    R.add("тест", "sunrise", {"agent": "a", "cmd": "1"})
    R.add("тест", "sunset", {"agent": "b", "cmd": "2"})
    rules = R.load()
    assert len(rules) == 1
    assert rules[0].event == "sunset"


def test_remove_existing():
    R.add("тест", "sunrise", {"agent": "x"})
    assert R.remove("тест") is True
    assert R.load() == []


def test_remove_unknown():
    assert R.remove("nope") is False


def test_match_event():
    R.add("a", "sunrise", {"agent": "x"})
    R.add("b", "sunset", {"agent": "y"})
    R.add("c", "sunrise", {"agent": "z"})
    assert len(R.match("sunrise")) == 2
    assert len(R.match("sunset")) == 1


def test_match_disabled():
    R.add("a", "sunrise", {"agent": "x"})
    rules = R.load()
    rules[0].enabled = False
    R.save(rules)
    assert R.match("sunrise") == []


def test_format_rules_empty():
    assert "нет" in R.format_rules().lower()


def test_format_rules_with_data():
    R.add("a", "sunrise", {"cmd": "утро"})
    out = R.format_rules()
    assert "a" in out
    assert "sunrise" in out


@pytest.mark.parametrize("text", [
    "правила", "список правил", "добавь правило", "если",
])
def test_can_handle(agent, req, text):
    assert agent.can_handle(req(text))


def test_cannot_handle_random(agent, req):
    assert not agent.can_handle(req("привет"))


@pytest.mark.asyncio
async def test_handle_list(agent, req):
    R.add("a", "sunrise", {"cmd": "утро"})
    resp = await agent.handle(req("список правил"))
    assert "sunrise" in resp.text


@pytest.mark.asyncio
async def test_handle_add_hint(agent, req):
    resp = await agent.handle(req("добавь правило"))
    assert "формат" in resp.text.lower() or "📝" in resp.text


@pytest.mark.asyncio
async def test_handle_remove(agent, req):
    R.add("тест", "sunrise", {"agent": "x"})
    resp = await agent.handle(req("удали правило тест"))
    assert "Удалено" in resp.text or "🗑" in resp.text
