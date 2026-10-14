"""#132 AgentScenes — тесты."""
from __future__ import annotations

import pytest

from aura.agents.scenes import AgentScenes, SCENES
from aura.core.protocol import AgentRequest


@pytest.fixture
def agent():
    return AgentScenes()


@pytest.fixture
def req():
    def _make(text: str):
        return AgentRequest(text=text, user="test")
    return _make


# === Константы ===

def test_scenes_not_empty():
    assert len(SCENES) >= 5


def test_scenes_have_commands():
    for name, cmds in SCENES.items():
        assert len(cmds) > 0, f"{name} пустая"
        for agent_name, cmd in cmds:
            assert agent_name
            assert cmd


def test_key_scenes_present():
    for expected in ("я спать", "доброе утро", "ухожу", "бодр"):
        if expected == "бодр":
            assert any("утро" in n for n in SCENES)
        else:
            assert any(expected in n for n in SCENES)


# === can_handle ===

@pytest.mark.parametrize("text", [
    "я спать", "Аура, я спать", "доброе утро", "ухожу",
    "я дома", "болит голова", "тревога",
])
def test_can_handle(agent, req, text):
    assert agent.can_handle(req(text))


def test_cannot_handle_random(agent, req):
    assert not agent.can_handle(req("привет как дела"))


# === handle ===

@pytest.mark.asyncio
async def test_handle_я_спать(agent, req):
    resp = await agent.handle(req("я спать"))
    assert "я спать" in resp.text.lower()
    assert "power" in resp.text
    assert "security" in resp.text


@pytest.mark.asyncio
async def test_handle_доброе_утро(agent, req):
    resp = await agent.handle(req("доброе утро"))
    assert "утро" in resp.text.lower()


@pytest.mark.asyncio
async def test_handle_тревога(agent, req):
    resp = await agent.handle(req("тревога"))
    assert "sos" in resp.text.lower()


@pytest.mark.asyncio
async def test_handle_not_matched(agent, req):
    resp = await agent.handle(req("привет"))
    # not_handled возвращает пустой/специальный ответ
    assert resp.text == "" or "not" in resp.text.lower() or resp.agent_name != "scenes"


# === list_scenes ===

def test_list_scenes(agent):
    out = agent.list_scenes()
    assert "я спать" in out
    assert "доброе утро" in out
    assert "тревога" in out


# === _run_scene ===

def test_run_scene_format(agent):
    out = agent._run_scene("тест", [("a", "b"), ("c", "d")])
    assert "тест" in out.text
    assert "1. [a] b" in out.text
    assert "2. [c] d" in out.text
