"""Тесты F-037 — SelfCheck agent.

Наука: Wiener 1948, Kanfer 1970, Duhigg 2012.
"""
from __future__ import annotations

import asyncio

from aura.agents.self_check import AgentSelfCheck


def test_agent_name():
    a = AgentSelfCheck()
    assert a.name == "self_check"


def test_can_handle():
    from aura.core.protocol import AgentRequest
    a = AgentSelfCheck()
    assert a.can_handle(AgentRequest(text="проверь себя"))
    assert a.can_handle(AgentRequest(text="статус системы"))
    assert not a.can_handle(AgentRequest(text="какая погода"))


def test_run_all_returns_dict():
    a = AgentSelfCheck()
    r = a._run_all()
    assert isinstance(r, dict)
    assert len(r) >= 5
    for k in ["microphone", "tts", "sqlcipher", "ollama", "disk"]:
        assert k in r


def test_format_report_all_ok():
    a = AgentSelfCheck()
    r = a._format_report({"a": True, "b": True})
    assert "✅" in r


def test_format_report_partial():
    a = AgentSelfCheck()
    r = a._format_report({"a": True, "b": False})
    assert "1/2" in r


def test_handle_returns_response():
    from aura.core.protocol import AgentRequest
    a = AgentSelfCheck()
    r = asyncio.run(a.handle(AgentRequest(text="проверь себя")))
    assert r.text
    assert r.agent_name == "self_check"
