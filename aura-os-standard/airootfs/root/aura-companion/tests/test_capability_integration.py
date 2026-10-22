"""Integration-тесты capability: Orchestrator.process_request + require().

Проверяем реальный execution path (раздел 8 промта):
    AgentRequest → Orchestrator → capability-check → agent.handle().

Наука (Д4): Saltzer & Schroeder 1975 (least privilege, default-deny).

API (из aura/core/protocol.py):
- AgentRequest(text, command, args, context, timestamp)
- AgentResponse(status, text, silent, data, error, agent_name)
- Registry.find(request) → первого агента с can_handle() == True.
"""
from __future__ import annotations

import pytest

from aura.core.capabilities import Profile, set_current
from aura.core.orchestrator import Orchestrator
from aura.core.protocol import AgentRequest, AgentResponse


class _FakeAgent:
    """Fake agent: всегда can_handle, считает вызовы."""
    def __init__(self, name: str):
        self.name = name
        self.calls = 0

    def can_handle(self, request: AgentRequest) -> bool:
        return True

    async def handle(self, request: AgentRequest) -> AgentResponse:
        self.calls += 1
        return AgentResponse.ok(
            text=f"handled by {self.name}",
            agent_name=self.name,
        )


class _FakeRegistry:
    """Возвращает одного конкретного агента."""
    def __init__(self, agent: _FakeAgent):
        self._agent = agent

    def find(self, request: AgentRequest):
        return self._agent

    def list_names(self):
        return [self._agent.name]

    def __len__(self):
        return 1


@pytest.fixture(autouse=True)
def _reset_profile():
    yield
    set_current(None)


def _make_orch(agent_name: str):
    agent = _FakeAgent(agent_name)
    orch = Orchestrator.__new__(Orchestrator)
    orch.registry = _FakeRegistry(agent)
    return orch, agent


@pytest.mark.asyncio
async def test_elder_cannot_call_shell():
    """Saltzer & Schroeder 1975: elder НЕ имеет shell:safe."""
    set_current(Profile(name="elder", base_class="elder"))
    orch, agent = _make_orch("shell")

    req = AgentRequest(text="rm -rf /")
    resp = await orch.process_request(req)

    assert agent.calls == 0, "SECURITY: shell был вызван для elder!"
    from aura.core.protocol import AgentStatus
    assert resp.status == AgentStatus.DENIED
    assert "не имеет доступа" in (resp.text or "")


@pytest.mark.asyncio
async def test_admin_can_call_shell():
    """Admin — wildcard '*' → shell разрешён."""
    set_current(Profile(name="admin", base_class="admin"))
    orch, agent = _make_orch("shell")

    req = AgentRequest(text="echo test")
    resp = await orch.process_request(req)

    assert agent.calls == 1, "admin должен иметь доступ к shell"
    assert "handled by shell" in (resp.text or "")


@pytest.mark.asyncio
async def test_elder_can_call_sos():
    """Базовое право elder — sos разрешён."""
    set_current(Profile(name="elder", base_class="elder"))
    orch, agent = _make_orch("sos")

    req = AgentRequest(text="мне плохо")
    resp = await orch.process_request(req)

    assert agent.calls == 1, "elder ДОЛЖЕН иметь доступ к sos"
    assert "handled by sos" in (resp.text or "")


@pytest.mark.asyncio
async def test_unmapped_agent_fail_open():
    """Раздел 20 промта: unmapped агент → fail-open (backward compat)."""
    set_current(Profile(name="elder", base_class="elder"))
    orch, agent = _make_orch("some_unknown_agent")

    req = AgentRequest(text="test")
    resp = await orch.process_request(req)

    assert agent.calls == 1, "unmapped агент должен пройти (fail-open)"


@pytest.mark.asyncio
async def test_no_profile_denies_mapped():
    """Fail-closed (Saltzer & Schroeder 1975): нет профиля → deny."""
    set_current(None)
    orch, agent = _make_orch("sos")

    req = AgentRequest(text="мне плохо")
    resp = await orch.process_request(req)

    assert agent.calls == 0, "без профиля — доступ запрещён"


@pytest.mark.asyncio
async def test_elder_medical_can_call_bpm():
    """elder + medical → bpm:read разрешён (trees)."""
    set_current(Profile(name="elder-medical", base_class="elder", trees=("medical",)))
    orch, agent = _make_orch("bpm")

    req = AgentRequest(text="какое давление")
    resp = await orch.process_request(req)

    assert agent.calls == 1, "elder+medical должен видеть bpm"
