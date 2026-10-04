"""
Тесты для AgentToolRouter.

Все вызовы urllib.request.urlopen — замоканы.
Живой Ollama НЕ вызывается.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from aura.agents.tool_router import AgentToolRouter


@pytest.fixture
def router():
    return AgentToolRouter()


def _mock_tool_call(tool_name, args):
    body = json.dumps({
        "message": {
            "tool_calls": [
                {"function": {"name": tool_name, "arguments": json.dumps(args)}}
            ]
        }
    }).encode("utf-8")
    mock = MagicMock()
    mock.read.return_value = body
    mock.__enter__ = lambda s: s
    mock.__exit__ = lambda s, *a: None
    return mock


def _mock_text(text):
    body = json.dumps({"message": {"content": text}}).encode("utf-8")
    mock = MagicMock()
    mock.read.return_value = body
    mock.__enter__ = lambda s: s
    mock.__exit__ = lambda s, *a: None
    return mock


# --- register ---

def test_register_adds_tool(router):
    router.register("test", "Test tool", {}, lambda: "ok")
    assert "test" in router.tools
    assert len(router.tool_defs) == 1


def test_register_tool_def_structure(router):
    router.register("get_time", "Time", {}, lambda: "12:00")
    td = router.tool_defs[0]
    assert td["type"] == "function"
    assert td["function"]["name"] == "get_time"
    assert td["function"]["description"] == "Time"


def test_register_with_params(router):
    router.register("play", "Play", {"query": "string"}, lambda query: query)
    td = router.tool_defs[0]
    assert "query" in td["function"]["parameters"]["properties"]
    assert td["function"]["parameters"]["required"] == ["query"]


# --- route: пустой реестр ---

def test_route_no_tools(router):
    assert router.route("привет") is None


# --- route: tool_calls ---

def test_route_tool_call(router):
    router.register("get_time", "Time", {}, lambda: "12:00")
    with patch("aura.agents.tool_router.urllib.request.urlopen",
               return_value=_mock_tool_call("get_time", {})):
        result = router.route("который час")
    assert result["type"] == "tool"
    assert result["tool"] == "get_time"
    assert result["response"] == "12:00"


def test_route_tool_call_with_args(router):
    router.register("play", "Play", {"query": "string"}, lambda query: f"playing {query}")
    with patch("aura.agents.tool_router.urllib.request.urlopen",
               return_value=_mock_tool_call("play", {"query": "rock"})):
        result = router.route("включи rock")
    assert result["type"] == "tool"
    assert result["args"] == {"query": "rock"}
    assert "playing rock" in result["response"]


def test_route_unknown_tool(router):
    router.register("known", "Known", {}, lambda: "ok")
    with patch("aura.agents.tool_router.urllib.request.urlopen",
               return_value=_mock_tool_call("unknown", {})):
        result = router.route("test")
    assert result["type"] == "error"
    assert "не найден" in result["response"]


# --- route: текстовый ответ ---

def test_route_text_response(router):
    router.register("test", "Test", {}, lambda: "ok")
    with patch("aura.agents.tool_router.urllib.request.urlopen",
               return_value=_mock_text("Не поняла команду")):
        result = router.route("xyz")
    assert result["type"] == "text"
    assert result["response"] == "Не поняла команду"


# --- route: ошибки ---

def test_route_handler_raises(router):
    def bad():
        raise RuntimeError("boom")
    router.register("bad", "Bad", {}, bad)
    with patch("aura.agents.tool_router.urllib.request.urlopen",
               return_value=_mock_tool_call("bad", {})):
        result = router.route("test")
    assert result["type"] == "tool"
    assert "boom" in result["response"]


def test_route_network_error(router):
    router.register("test", "Test", {}, lambda: "ok")
    with patch("aura.agents.tool_router.urllib.request.urlopen",
               side_effect=Exception("network down")):
        result = router.route("test")
    assert result["type"] == "error"
    assert "network down" in result["response"]


# --- конфигурация ---

def test_constants(router):
    assert router.MODEL == "qwen2.5:7b-instruct-q4_K_M"
    assert "11434" in router.OLLAMA_URL
    assert router.TIMEOUT == 30


def test_system_prompt_russian(router):
    assert "русском" in router.SYSTEM_PROMPT
