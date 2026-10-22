"""
Тесты для AgentRegistry (memory_registry).

Работаем с временным файлом через monkeypatch.
Живой ~/aura_project/memory_registry.json НЕ трогаем.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aura.agents.registry import AgentRegistry
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def registry(tmp_path, monkeypatch):
    """AgentRegistry с временным memory-файлом."""
    test_file = tmp_path / "registry_test.json"
    monkeypatch.setattr(AgentRegistry, "MEMORY_FILE", str(test_file))
    return AgentRegistry()


@pytest.fixture
def registry_with_events(registry):
    """Реестр с уже записанными событиями."""
    registry.log("command", {"command": "который час"})
    registry.log("command", {"command": "погода в Москве"})
    registry.log("dialog", {"user": "привет", "aura": "привет"})
    return registry


# --- can_handle ---

def test_can_handle_show_memory(registry):
    assert registry.can_handle(AgentRequest(text="покажи память"))


def test_can_handle_what_in_memory(registry):
    assert registry.can_handle(AgentRequest(text="что в памяти"))


def test_can_handle_show_context(registry):
    assert registry.can_handle(AgentRequest(text="покажи контекст"))


def test_can_handle_registry(registry):
    assert registry.can_handle(AgentRequest(text="реестр памяти"))


def test_cannot_handle_time(registry):
    assert not registry.can_handle(AgentRequest(text="который час"))


def test_cannot_handle_empty(registry):
    assert not registry.can_handle(AgentRequest(text=""))


# --- log ---

def test_log_command_creates_file(registry):
    registry.log("command", {"command": "test"})
    assert Path(registry.memory_file).exists()


def test_log_increments_total_commands(registry):
    registry.log("command", {"command": "a"})
    registry.log("command", {"command": "b"})
    assert registry.session_data["summary"]["total_commands"] == 2


def test_log_tracks_most_used(registry):
    registry.log("command", {"command": "который час"})
    registry.log("command", {"command": "который час"})
    registry.log("command", {"command": "погода"})

    most_used = registry.session_data["summary"]["most_used"]
    assert most_used["который час"] == 2
    assert most_used["погода"] == 1


def test_log_dialog_does_not_increment_commands(registry):
    registry.log("dialog", {"user": "a", "aura": "b"})
    assert registry.session_data["summary"]["total_commands"] == 0


# --- get_last ---

def test_get_last_returns_events(registry_with_events):
    last = registry_with_events.get_last(2)
    assert len(last) == 2


def test_get_last_returns_all(registry_with_events):
    last = registry_with_events.get_last(10)
    assert len(last) == 3


# --- get_context ---

def test_get_context_last_command(registry_with_events):
    ctx = registry_with_events.get_context()
    assert ctx["last_command"] == "погода в Москве"


def test_get_context_recent_commands(registry_with_events):
    ctx = registry_with_events.get_context()
    assert "который час" in ctx["recent_commands"]
    assert "погода в Москве" in ctx["recent_commands"]


def test_get_context_last_dialog(registry_with_events):
    ctx = registry_with_events.get_context()
    assert ctx["last_dialog"] == {"user": "привет", "aura": "привет"}


def test_get_context_empty(registry):
    ctx = registry.get_context()
    assert ctx["last_command"] is None
    assert ctx["last_dialog"] is None
    assert ctx["recent_commands"] == []


# --- handle ---

@pytest.mark.asyncio
async def test_handle_show_memory(registry_with_events):
    resp = await registry_with_events.handle(AgentRequest(text="покажи память"))

    assert resp.status == AgentStatus.OK
    assert resp.agent_name == "registry"
    # Возвращает JSON, обрезанный до 500 символов
    assert "last_command" in resp.text


@pytest.mark.asyncio
async def test_handle_show_context(registry_with_events):
    resp = await registry_with_events.handle(AgentRequest(text="покажи контекст"))

    assert resp.status == AgentStatus.OK
    assert "last_command" in resp.text


@pytest.mark.asyncio
async def test_handle_not_handled(registry):
    resp = await registry.handle(AgentRequest(text="просто болтовня"))
    assert resp.status == AgentStatus.NOT_HANDLED


# --- persistence ---

def test_load_existing_file(tmp_path, monkeypatch):
    """Если файл есть — загружаем его."""
    test_file = tmp_path / "existing.json"
    test_file.write_text(
        json.dumps({
            "session_id": "test",
            "start_time": "2026-01-01",
            "events": [{"time": "t", "type": "command", "data": {"command": "x"}}],
            "summary": {"total_commands": 1, "most_used": {"x": 1}, "patterns": []},
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(AgentRegistry, "MEMORY_FILE", str(test_file))
    r = AgentRegistry()

    assert r.session_data["session_id"] == "test"
    assert len(r.session_data["events"]) == 1


def test_corrupted_file_creates_new_session(tmp_path, monkeypatch):
    """Если файл битый — создаём новую сессию, не падаем."""
    test_file = tmp_path / "corrupted.json"
    test_file.write_text("{ broken json", encoding="utf-8")
    monkeypatch.setattr(AgentRegistry, "MEMORY_FILE", str(test_file))
    r = AgentRegistry()

    assert "session_id" in r.session_data
    assert r.session_data["events"] == []
