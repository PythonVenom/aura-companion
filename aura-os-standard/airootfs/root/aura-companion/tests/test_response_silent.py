"""Тесты ADR-048: silent-политика озвучки."""
import asyncio
import pytest
from aura.core.protocol import AgentRequest, AgentResponse, AgentStatus
from aura.core.orchestrator import Orchestrator
from aura.agents.music_local import AgentMusicLocal


def test_silent_default_false():
    r = AgentResponse.ok("test")
    assert r.silent is False


def test_silent_true_explicit():
    r = AgentResponse.ok("test", silent=True)
    assert r.silent is True


def test_silent_not_in_error():
    # Через явный конструктор (pydantic v2 конфликтует field.error vs classmethod.error)
    r = AgentResponse(status=AgentStatus.ERROR, error="ошибка")
    assert r.silent is False


def test_orchestrator_last_silent_initial():
    o = Orchestrator()
    assert o.last_silent() is False


def test_orchestrator_last_silent_after_silent_response():
    o = Orchestrator()
    o._last_response = AgentResponse.ok("x", silent=True)
    assert o.last_silent() is True


def test_orchestrator_last_silent_after_normal():
    o = Orchestrator()
    o._last_response = AgentResponse.ok("x", silent=False)
    assert o.last_silent() is False


def test_music_next_is_silent():
    m = AgentMusicLocal()
    r = asyncio.run(m.handle(AgentRequest(text="следующий трек")))
    assert r.silent is True


def test_music_list_tracks_not_silent():
    m = AgentMusicLocal()
    r = asyncio.run(m.handle(AgentRequest(text="список треков")))
    assert r.silent is False
