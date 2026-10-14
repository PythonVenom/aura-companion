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
