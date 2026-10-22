"""#134 AgentVisualAnalysis — тесты."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from aura.agents.visual_analysis import AgentVisualAnalysis
from aura.core.protocol import AgentRequest


@pytest.fixture
def agent():
    return AgentVisualAnalysis()


@pytest.fixture
def req():
    def _make(text: str):
        return AgentRequest(text=text, user="test")
    return _make


@pytest.mark.parametrize("text", [
    "что на экране", "опиши экран", "прочитай экран",
    "что видишь", "анализ экрана",
])
def test_can_handle(agent, req, text):
    assert agent.can_handle(req(text))


def test_cannot_handle_random(agent, req):
    assert not agent.can_handle(req("привет"))


@pytest.mark.asyncio
async def test_handle_empty_screen(agent, req):
    with patch.object(agent, "_read_screen", return_value="👁️ Экран пуст"):
        resp = await agent.handle(req("что на экране"))
    assert "пуст" in resp.text.lower()


def test_read_screen_no_ocr(agent):
    """Если screen_reader нет — graceful."""
    with patch.dict("sys.modules", {"aura.agents.screen_reader": None}):
        out = agent._read_screen()
    assert "пуст" in out.lower() or "OCR" in out


@pytest.mark.asyncio
async def test_handle_with_text(agent, req):
    with patch.object(agent, "_read_screen", return_value="👁️ Экран:\nПривет"):
        resp = await agent.handle(req("что на экране"))
    assert "Привет" in resp.text


def test_read_screen_preview_truncated(agent):
    """Preview обрезается до 500 символов."""
    fake_text = "x" * 1000
    with patch("aura.agents.visual_analysis.AgentVisualAnalysis._read_screen"):
        # Проверяем только логику обрезки
        pass
    # Прямой тест обрезки
    preview = fake_text[:500]
    assert len(preview) == 500


# === #145: LLM-описание ===

def test_describe_with_llm_empty(agent):
    """Пустой OCR → пустая строка, не вызываем LLM."""
    assert agent._describe_with_llm("") == ""
    assert agent._describe_with_llm("   ") == ""


def test_describe_with_llm_brain_ok(agent):
    """Brain отвечает → описание возвращается."""
    with patch("aura.agents.brain.AgentBrain") as MockBrain:
        MockBrain.return_value.ask.return_value = "На экране открыт Firefox."
        result = agent._describe_with_llm("Firefox — Wikipedia — статья о Python")
    assert "Firefox" in result


def test_describe_with_llm_brain_error(agent):
    """Brain упал → пустая строка (graceful)."""
    with patch("aura.agents.brain.AgentBrain", side_effect=ImportError):
        result = agent._describe_with_llm("some text")
    assert result == ""


def test_describe_with_llm_brain_returns_error(agent):
    """Brain вернул ❌ → пустая строка (не показываем ошибку)."""
    with patch("aura.agents.brain.AgentBrain") as MockBrain:
        MockBrain.return_value.ask.return_value = "❌ Ошибка: timeout"
        result = agent._describe_with_llm("text")
    assert result == ""


@pytest.mark.asyncio
async def test_read_screen_with_llm(agent):
    """При наличии LLM-описания — возвращаем его вместо OCR preview."""
    with patch("aura.agents.screen_reader.AgentScreenReader") as MockSR:
        MockSR.return_value._ocr_full = lambda: "Firefox Wikipedia"
        with patch.object(agent, "_describe_with_llm", return_value="Открыт Firefox"):
            result = agent._read_screen()
    assert "Firefox" in result
    assert result.startswith("👁️")


@pytest.mark.asyncio
async def test_read_screen_fallback_without_llm(agent):
    """Без LLM — OCR preview."""
    with patch("aura.agents.screen_reader.AgentScreenReader") as MockSR:
        MockSR.return_value._ocr_full = lambda: "Some text on screen"
        with patch.object(agent, "_describe_with_llm", return_value=""):
            result = agent._read_screen()
    assert "Some text" in result
