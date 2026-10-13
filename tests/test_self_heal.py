"""#104 AgentSelfHeal — тесты."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.self_heal import AgentSelfHeal
from aura.core.protocol import AgentRequest


@pytest.fixture
def agent():
    return AgentSelfHeal()


@pytest.fixture
def req():
    def _make(text: str):
        return AgentRequest(text=text, user="test")
    return _make


# === can_handle ===

@pytest.mark.parametrize("text", [
    "почини себя", "что с тобой", "самодиагностика",
    "почему тормозишь", "почему долго думаешь",
])
def test_can_handle(agent, req, text):
    assert agent.can_handle(req(text))


def test_cannot_handle_random(agent, req):
    assert not agent.can_handle(req("привет как дела"))


# === _check_memory ===

def test_check_memory_positive(agent):
    mb = agent._check_memory()
    assert mb > 0


def test_check_memory_reasonable(agent):
    mb = agent._check_memory()
    assert mb < 10_000


# === _check_media_state ===

def test_check_media_state_none(agent, tmp_path, monkeypatch):
    from aura.agents import media_state
    monkeypatch.setattr(media_state, "STATE_PATH", tmp_path / "state.json")
    assert agent._check_media_state() == "none"


def test_check_media_state_vk(agent, tmp_path, monkeypatch):
    from aura.agents import media_state
    monkeypatch.setattr(media_state, "STATE_PATH", tmp_path / "state.json")
    media_state.set_active("vk")
    assert agent._check_media_state() == "vk"


# === _check_llm_timeout ===

def test_check_llm_timeout_default(agent, monkeypatch):
    monkeypatch.delenv("AURA_LLM_TIMEOUT", raising=False)
    assert agent._check_llm_timeout() == 8


def test_check_llm_timeout_env(agent, monkeypatch):
    monkeypatch.setenv("AURA_LLM_TIMEOUT", "15")
    assert agent._check_llm_timeout() == 15


def test_check_llm_timeout_bad_env(agent, monkeypatch):
    monkeypatch.setenv("AURA_LLM_TIMEOUT", "abc")
    assert agent._check_llm_timeout() == 8


# === diagnose ===

def test_diagnose_all_ok(agent):
    with patch.object(agent, "_check_memory", return_value=100):
        with patch.object(agent, "_check_media_state", return_value="none"):
            with patch.object(agent, "_check_agents", return_value=96):
                with patch.object(agent, "_check_ollama", return_value=True):
                    with patch.object(agent, "_check_llm_timeout", return_value=8):
                        report = agent.diagnose()
    assert "Всё в порядке" in report


def test_diagnose_high_memory(agent):
    with patch.object(agent, "_check_memory", return_value=600):
        with patch.object(agent, "_check_media_state", return_value="none"):
            with patch.object(agent, "_check_agents", return_value=96):
                with patch.object(agent, "_check_ollama", return_value=True):
                    with patch.object(agent, "_check_llm_timeout", return_value=8):
                        report = agent.diagnose()
    assert "Память" in report
    assert "600" in report


def test_diagnose_vk_stuck(agent):
    with patch.object(agent, "_check_memory", return_value=100):
        with patch.object(agent, "_check_media_state", return_value="vk"):
            with patch.object(agent, "_check_agents", return_value=96):
                with patch.object(agent, "_check_ollama", return_value=True):
                    with patch.object(agent, "_check_llm_timeout", return_value=8):
                        report = agent.diagnose()
    assert "media_state" in report


def test_diagnose_ollama_down(agent):
    with patch.object(agent, "_check_memory", return_value=100):
        with patch.object(agent, "_check_media_state", return_value="none"):
            with patch.object(agent, "_check_agents", return_value=96):
                with patch.object(agent, "_check_ollama", return_value=False):
                    with patch.object(agent, "_check_llm_timeout", return_value=8):
                        report = agent.diagnose()
    assert "Ollama" in report


# === handle ===

@pytest.mark.asyncio
async def test_handle_returns_report(agent, req):
    with patch.object(agent, "diagnose", return_value="🩺 OK"):
        resp = await agent.handle(req("почини себя"))
    assert resp.text == "🩺 OK"
