"""
Тесты для AgentBrain.

Все вызовы urllib.request.urlopen — замоканы.
Живой Ollama НЕ вызывается.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from aura.agents.brain import AgentBrain


@pytest.fixture
def brain():
    return AgentBrain()


def _mock_urlopen(response_text):
    """Мок urlopen, возвращающий Ollama-ответ."""
    body = json.dumps({
        "message": {"role": "assistant", "content": response_text}
    }).encode("utf-8")

    mock = MagicMock()
    mock.read.return_value = body
    mock.__enter__ = lambda s: s
    mock.__exit__ = lambda s, *a: None
    return mock


# --- ask: базовые сценарии ---

def test_ask_returns_response(brain):
    with patch("aura.agents.brain.urllib.request.urlopen", return_value=_mock_urlopen("Привет, Создатель")):
        result = brain.ask("привет")
    assert result == "Привет, Создатель"


def test_ask_handles_empty_content(brain):
    body = json.dumps({"message": {}}).encode("utf-8")
    mock = MagicMock()
    mock.read.return_value = body
    mock.__enter__ = lambda s: s
    mock.__exit__ = lambda s, *a: None
    with patch("aura.agents.brain.urllib.request.urlopen", return_value=mock):
        result = brain.ask("привет")
    assert "не поняла" in result.lower()


def test_ask_handles_network_error(brain):
    with patch("aura.agents.brain.urllib.request.urlopen", side_effect=Exception("network down")):
        result = brain.ask("привет")
    assert "Ошибка" in result
    assert "network down" in result


# --- история ---

def test_ask_appends_to_history(brain):
    with patch("aura.agents.brain.urllib.request.urlopen", return_value=_mock_urlopen("ответ")):
        brain.ask("вопрос")
    assert len(brain.context_history) == 2
    assert brain.context_history[0]["role"] == "user"
    assert brain.context_history[0]["content"] == "вопрос"
    assert brain.context_history[1]["role"] == "assistant"
    assert brain.context_history[1]["content"] == "ответ"


def test_ask_history_limited_to_max(brain):
    with patch("aura.agents.brain.urllib.request.urlopen", return_value=_mock_urlopen("ответ")):
        for i in range(15):
            brain.ask(f"вопрос {i}")
    assert len(brain.context_history) <= brain.MAX_HISTORY + 1  # паритет с монолитом


def test_ask_on_error_does_not_append_assistant(brain):
    with patch("aura.agents.brain.urllib.request.urlopen", side_effect=Exception("fail")):
        brain.ask("вопрос")
    # user добавлен, assistant — нет
    assert len(brain.context_history) == 1
    assert brain.context_history[0]["role"] == "user"


# --- конфигурация ---

def test_brain_constants(brain):
    assert brain.MODEL == "qwen2.5:7b-instruct-q4_K_M"
    assert "11434" in brain.OLLAMA_URL
    assert brain.TIMEOUT == 30
    assert brain.MAX_HISTORY == 10


def test_system_prompt_russian(brain):
    assert "русском" in brain.SYSTEM_PROMPT
    assert "Аура" in brain.SYSTEM_PROMPT


def test_ask_sends_correct_model(brain):
    captured = {}
    def capture(req, timeout):
        captured["data"] = json.loads(req.data.decode("utf-8"))
        captured["url"] = req.full_url
        return _mock_urlopen("ok")
    with patch("aura.agents.brain.urllib.request.urlopen", side_effect=capture):
        brain.ask("тест")
    assert captured["url"] == brain.OLLAMA_URL
    assert captured["data"]["model"] == brain.MODEL
    assert captured["data"]["stream"] is False
    assert captured["data"]["options"]["temperature"] == 0.7
