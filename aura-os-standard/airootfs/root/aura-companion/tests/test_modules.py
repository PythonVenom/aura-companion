"""Блок 6 — тесты AgentModules."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from aura.agents.modules import AgentModules, CATEGORIES, _category
from aura.core.protocol import AgentRequest


@pytest.fixture
def agent():
    return AgentModules()


@pytest.fixture
def req():
    def _make(text: str):
        return AgentRequest(text=text, user="test")
    return _make


# === _category ===

def test_category_time():
    assert _category("AgentTime") == "🕐 Простые"


def test_category_sos():
    assert _category("AgentSOS") == "🏥 Elder-care"


def test_category_wine():
    assert _category("AgentWineLauncher") == "🔧 Наши новые"


def test_category_unknown():
    assert _category("AgentAlien") == "❓ Прочее"


def test_category_strips_agent_prefix():
    assert _category("AgentAudioPult") == "🔊 Audio"


# === can_handle ===

@pytest.mark.parametrize("text", [
    "список модулей", "какие агенты", "аура модули", "сколько агентов",
])
def test_can_handle(agent, req, text):
    assert agent.can_handle(req(text))


def test_cannot_handle_random(agent, req):
    assert not agent.can_handle(req("привет как дела"))


# === handle ===

@pytest.mark.asyncio
async def test_handle_no_orchestrator(agent, req):
    resp = await agent.handle(req("список модулей"))
    assert "не подключён" in resp.text


@pytest.mark.asyncio
async def test_handle_groups_by_category(agent, req):
    """Mock orchestrator с 4 агентами."""
    orch = MagicMock()
    orch.registry.list_names.return_value = [
        "time", "sos", "wine_launcher", "audio_pult", "plugin_test",
    ]
    agent.orchestrator = orch
    resp = await agent.handle(req("список модулей"))
    assert "4 агентов" in resp.text or "4 " in resp.text  # плагин исключён
    assert "Про" in resp.text  # категория "Простые"
    assert "Elder-care" in resp.text


@pytest.mark.asyncio
async def test_handle_excludes_plugins(agent, req):
    orch = MagicMock()
    orch.registry.list_names.return_value = [
        "time", "plugin_a", "plugin_b",
    ]
    agent.orchestrator = orch
    resp = await agent.handle(req("список"))
    assert "plugin" not in resp.text


@pytest.mark.asyncio
async def test_handle_registry_error(agent, req):
    orch = MagicMock()
    orch.registry.list_names.side_effect = RuntimeError("boom")
    agent.orchestrator = orch
    resp = await agent.handle(req("список модулей"))
    assert "❌" in resp.text


# === CATEGORIES ===

def test_categories_count():
    """Минимум 10 категорий."""
    assert len(CATEGORIES) >= 10


def test_categories_no_overlap_for_key_agents():
    """Time, SOS, WineLauncher в разных категориях."""
    cats = {_category(x) for x in ("AgentTime", "AgentSOS", "AgentWineLauncher")}
    assert len(cats) == 3
