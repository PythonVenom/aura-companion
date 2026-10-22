"""Тесты AgentOpenResolver."""
from __future__ import annotations
from aura.agents.open_resolver import AgentOpenResolver, WEB_MAP
from aura.core.protocol import AgentRequest


def test_web_map():
    assert "дипсик" in WEB_MAP
    assert "вк" in WEB_MAP


def test_can_handle():
    a = AgentOpenResolver()
    assert a.can_handle(AgentRequest(text="открой вк"))
    assert a.can_handle(AgentRequest(text="запусти firefox"))
    assert not a.can_handle(AgentRequest(text="который час"))


def test_extract_target():
    a = AgentOpenResolver()
    assert a._target("открой дипсик") == "дипсик"
    assert a._target("открой вк") == "вк"
    assert a._target("запусти firefox") == "firefox"


def test_target_empty():
    a = AgentOpenResolver()
    assert a._target("открой") == ""
