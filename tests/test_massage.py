"""MassageSessionAgent (ADR-044)."""
import pytest
from unittest.mock import patch

from aura.agents.massage import AgentMassage, Session
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def agent():
    return AgentMassage()


def _req(text):
    return AgentRequest(text=text)


# --- Session dataclass ---

def test_session_ends_at():
    s = Session(client="Иванов", duration_min=50)
    assert s.ends_at > s.started_at


def test_session_remaining():
    s = Session(client="X", duration_min=50)
    # сразу после старта ~50 мин
    assert s.remaining_min in (49, 50)


# --- can_handle ---

def test_can_handle_session(agent):
    assert agent.can_handle(_req("сессия Иванов 50")) is True


def test_can_handle_note(agent):
    assert agent.can_handle(_req("запиши спина L4-L5")) is True


def test_can_handle_history(agent):
    assert agent.can_handle(_req("что было с Ивановым")) is True


def test_can_handle_negative(agent):
    assert agent.can_handle(_req("погода в Москве")) is False


# --- handle: start ---

@pytest.mark.asyncio
async def test_start_session(agent):
    r = await agent.handle(_req("сессия Иванов 50"))
    assert r.status == AgentStatus.OK
    assert "Иванов" in r.text
    assert "50" in r.text
    assert agent._current is not None
    assert agent._current.client == "Иванов"
    assert agent._current.duration_min == 50


@pytest.mark.asyncio
async def test_start_no_match(agent):
    r = await agent.handle(_req("сессия"))
    assert r.status == AgentStatus.OK
    assert "Скажи" in r.text
    assert agent._current is None


# --- handle: note ---

@pytest.mark.asyncio
async def test_note_without_session(agent):
    r = await agent.handle(_req("запиши спина"))
    assert "Сначала" in r.text
    assert agent._current is None


@pytest.mark.asyncio
async def test_note_with_session(agent):
    await agent.handle(_req("сессия Иванов 50"))
    r = await agent.handle(_req("запиши спина L4-L5 напряжение"))
    assert "Записал" in r.text
    assert "спина" in agent._current.notes


# --- handle: history ---

@pytest.mark.asyncio
async def test_history(agent):
    r = await agent.handle(_req("что было с Ивановым"))
    assert r.status == AgentStatus.OK
    assert "Иванов" in r.text


# --- handle: finish ---

@pytest.mark.asyncio
async def test_finish_without_session(agent):
    r = await agent.handle(_req("закончить сессию"))
    assert "Нет активной" in r.text


@pytest.mark.asyncio
async def test_finish_with_session(agent):
    await agent.handle(_req("сессия Иванов 50"))
    r = await agent.handle(_req("закончить сессию"))
    assert "завершена" in r.text
    assert agent._current is None


# --- handle: not handled ---

@pytest.mark.asyncio
async def test_not_handled(agent):
    r = await agent.handle(_req("погода"))
    assert r.status == AgentStatus.NOT_HANDLED
