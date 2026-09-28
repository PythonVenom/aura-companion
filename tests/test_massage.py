"""MassageSessionAgent (ADR-044)."""
import pytest
from datetime import datetime

from aura.agents import massage as mmod
from aura.agents.massage import AgentMassage, Session
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def agent(tmp_path, monkeypatch):
    """Изолированный CLIENTS_DIR для каждого теста."""
    monkeypatch.setattr(mmod, "CLIENTS_DIR", tmp_path / "clients")
    return AgentMassage()


def _req(text):
    return AgentRequest(text=text)


# --- Session dataclass ---

def test_session_ends_at():
    s = Session(client="Иванов", duration_min=50)
    assert s.ends_at > s.started_at


def test_session_remaining():
    s = Session(client="X", duration_min=50)
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


# --- start ---

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


@pytest.mark.asyncio
async def test_start_writes_client_file(agent, tmp_path):
    """Bug B: start сохраняет в файл клиента."""
    await agent.handle(_req("сессия Тест 30"))
    f = tmp_path / "clients" / "тест.md"
    assert f.exists()
    content = f.read_text(encoding="utf-8")
    assert "начало сессии" in content


@pytest.mark.asyncio
async def test_client_name_title(agent):
    """Bug A: 'тест_клиент' -> 'Тест_Клиент'."""
    await agent.handle(_req("сессия тест_клиент 30"))
    assert agent._current.client == "Тест_Клиент"


# --- note ---

@pytest.mark.asyncio
async def test_note_without_session(agent):
    r = await agent.handle(_req("запиши спина"))
    assert "Сначала" in r.text


@pytest.mark.asyncio
async def test_note_with_session(agent, tmp_path):
    await agent.handle(_req("сессия Иванов 50"))
    r = await agent.handle(_req("запиши спина L4-L5 напряжение"))
    assert "Записал" in r.text
    assert "спина" in agent._current.notes
    # Проверяем файл
    f = tmp_path / "clients" / "иванов.md"
    content = f.read_text(encoding="utf-8")
    assert "спина" in content


# --- history (Bug C) ---

@pytest.mark.asyncio
async def test_history_empty(agent):
    """Bug C: пустая история -> честное сообщение."""
    r = await agent.handle(_req("что было с Неизвестный"))
    assert r.status == AgentStatus.OK
    assert "пока нет записей" in r.text


@pytest.mark.asyncio
async def test_history_after_session(agent):
    """Bug C: history читает только записи клиента, не весь RAG."""
    await agent.handle(_req("сессия Петров 45"))
    r = await agent.handle(_req("что было с Петров"))
    assert "Петров" in r.text
    assert "начало сессии" in r.text


# --- finish ---

@pytest.mark.asyncio
async def test_finish_without_session(agent):
    r = await agent.handle(_req("закончить сессию"))
    assert "Нет активной" in r.text


@pytest.mark.asyncio
async def test_finish_with_session(agent, tmp_path):
    await agent.handle(_req("сессия Иванов 50"))
    await agent.handle(_req("запиши шея"))
    r = await agent.handle(_req("закончить сессию"))
    assert "завершена" in r.text
    assert agent._current is None
    # Финальная сводка в файле
    f = tmp_path / "clients" / "иванов.md"
    content = f.read_text(encoding="utf-8")
    assert "45мин" in content or "сессия" in content.lower()


# --- not handled ---

@pytest.mark.asyncio
async def test_not_handled(agent):
    r = await agent.handle(_req("погода"))
    assert r.status == AgentStatus.NOT_HANDLED
