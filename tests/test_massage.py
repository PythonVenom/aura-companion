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


# --- RAG integration (mock) ---

class _FakeRAG:
    """Fake RAG для тестов без ChromaDB."""
    def __init__(self):
        self.saved = []
        self.search_result = "прошлый раз: спина L4-L5"

    def remember(self, user_text, aura_response):
        self.saved.append((user_text, aura_response))
        return "ok"

    def search(self, query, n_results=3):
        return self.search_result


@pytest.fixture
def agent_with_rag():
    a = AgentMassage()
    a._rag = _FakeRAG()
    return a


@pytest.mark.asyncio
async def test_note_saves_to_rag(agent_with_rag):
    await agent_with_rag.handle(_req("сессия Иванов 50"))
    await agent_with_rag.handle(_req("запиши спина L4-L5"))
    fake = agent_with_rag._rag
    assert len(fake.saved) == 1
    assert "Иванов" in fake.saved[0][0]
    assert "спина" in fake.saved[0][0]


@pytest.mark.asyncio
async def test_history_reads_from_rag(agent_with_rag):
    r = await agent_with_rag.handle(_req("что было с Ивановым"))
    assert "Иванов" in r.text
    assert "L4-L5" in r.text


@pytest.mark.asyncio
async def test_finish_saves_summary(agent_with_rag):
    await agent_with_rag.handle(_req("сессия Петров 45"))
    await agent_with_rag.handle(_req("запиши шея напряжение"))
    r = await agent_with_rag.handle(_req("закончить"))
    assert "завершена" in r.text
    fake = agent_with_rag._rag
    # 2 записи: заметка + финальная сводка
    assert len(fake.saved) == 2
    assert "45мин" in fake.saved[1][0]


@pytest.mark.asyncio
async def test_rag_unavailable(agent):
    """Если RAG не инициализируется — не падаем, деградируем."""
    agent._rag = False  # marker: не удалось
    r = await agent.handle(_req("что было с Ивановым"))
    assert r.status == AgentStatus.OK
    assert "RAG недоступен" in r.text


@pytest.mark.asyncio
async def test_note_without_rag_still_saves_locally(agent):
    """Без RAG — заметка всё равно в self._current.notes."""
    agent._rag = False
    await agent.handle(_req("сессия Сидоров 30"))
    await agent.handle(_req("запиши колено"))
    assert "колено" in agent._current.notes


# --- Bugfix (live-test) ---

@pytest.mark.asyncio
async def test_start_saves_to_rag():
    """Bug B: start должен сохранять сессию в RAG."""
    a = AgentMassage()
    a._rag = _FakeRAG()
    await a.handle(_req("сессия Тест_Клиент 30"))
    assert len(a._rag.saved) == 1
    assert "начало сессии" in a._rag.saved[0][0]


@pytest.mark.asyncio
async def test_client_name_title():
    """Bug A: 'тест_клиент' -> 'Тест_Клиент' (не 'Тест_клиент')."""
    a = AgentMassage()
    await a.handle(_req("сессия тест_клиент 30"))
    assert a._current.client == "Тест_Клиент"
