"""
Тесты для AgentRAGMemory.

Никаких живых вызовов к ChromaDB или Ollama.
Всё мокается:
- _init_chroma — чтобы не создавать реальную базу
- _get_embedding — чтобы не звать Ollama
- collection — MagicMock вместо настоящей коллекции

Проверяем:
- can_handle ловит команды и не ловит лишние
- handle разбирает команды и возвращает AgentResponse
- remember / search / get_stats / clear возвращают разумные строки
- поведение при ready=False (агент не упал, вернул ошибку)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.rag_memory import AgentRAGMemory
from aura.core.protocol import AgentRequest, AgentStatus


# --- Фикстура: готовый агент с замоканным chroma ---

@pytest.fixture
def rag():
    """AgentRAGMemory с отключённым _init_chroma и мок-коллекцией."""
    with patch.object(AgentRAGMemory, "_init_chroma"):
        r = AgentRAGMemory()

    r.ready = True
    r.client = MagicMock()
    r.collection = MagicMock()
    r.collection.count.return_value = 5
    return r


@pytest.fixture
def rag_not_ready():
    """AgentRAGMemory в состоянии ready=False."""
    with patch.object(AgentRAGMemory, "_init_chroma"):
        r = AgentRAGMemory()
    r.ready = False
    return r


# --- can_handle ---

def test_can_handle_remember(rag):
    assert rag.can_handle(AgentRequest(text="вспомни про космос"))


def test_can_handle_what_i_said(rag):
    assert rag.can_handle(AgentRequest(text="что я говорил про музыку"))


def test_can_handle_stats(rag):
    assert rag.can_handle(AgentRequest(text="статистика памяти"))


def test_can_handle_clear(rag):
    assert rag.can_handle(AgentRequest(text="очисти память"))


def test_cannot_handle_unrelated(rag):
    assert not rag.can_handle(AgentRequest(text="который час"))


def test_cannot_handle_empty(rag):
    assert not rag.can_handle(AgentRequest(text=""))


# --- handle: статистика ---

@pytest.mark.asyncio
async def test_handle_stats(rag):
    resp = await rag.handle(AgentRequest(text="статистика памяти"))
    assert resp.status == AgentStatus.OK
    assert resp.agent_name == "rag_memory"
    assert "5" in resp.text


@pytest.mark.asyncio
async def test_handle_stats_not_ready(rag_not_ready):
    resp = await rag_not_ready.handle(AgentRequest(text="статистика памяти"))
    assert resp.status == AgentStatus.OK
    assert "не готова" in resp.text


# --- handle: очистка ---

@pytest.mark.asyncio
async def test_handle_clear(rag):
    resp = await rag.handle(AgentRequest(text="очисти память"))
    assert resp.status == AgentStatus.OK
    assert "очищена" in resp.text.lower()
    assert rag.client.delete_collection.called


# --- handle: поиск ---

@pytest.mark.asyncio
async def test_handle_search_with_query(rag):
    with patch.object(rag, "_get_embedding", return_value=[0.1, 0.2]):
        rag.collection.query.return_value = {
            "documents": [["Пользователь: привет\nАура: привет"]],
            "metadatas": [[{"timestamp": "2026-09-20T12:00:00"}]],
        }
        resp = await rag.handle(AgentRequest(text="вспомни привет"))

    assert resp.status == AgentStatus.OK
    assert "1 воспоминаний" in resp.text or "1 воспоминание" in resp.text
    assert "привет" in resp.text


@pytest.mark.asyncio
async def test_handle_search_empty_query(rag):
    resp = await rag.handle(AgentRequest(text="вспомни"))
    assert resp.status == AgentStatus.OK
    assert "Что вспомнить" in resp.text


@pytest.mark.asyncio
async def test_handle_search_empty_memory(rag):
    rag.collection.count.return_value = 0
    resp = await rag.handle(AgentRequest(text="вспомни космос"))
    assert resp.status == AgentStatus.OK
    assert "пуста" in resp.text.lower()


# --- handle: not_handled ---

@pytest.mark.asyncio
async def test_handle_not_handled(rag):
    resp = await rag.handle(AgentRequest(text="просто болтовня"))
    assert resp.status == AgentStatus.NOT_HANDLED


# --- remember (публичный, событие) ---

def test_remember_ok(rag):
    with patch.object(rag, "_get_embedding", return_value=[0.1] * 768):
        result = rag.remember("привет", "привет, Создатель")

    assert "Запомнила" in result
    assert rag.collection.add.called


def test_remember_no_embedding(rag):
    with patch.object(rag, "_get_embedding", return_value=None):
        result = rag.remember("привет", "привет")

    assert "эмбеддинг" in result.lower()


def test_remember_not_ready(rag_not_ready):
    result = rag_not_ready.remember("привет", "привет")
    assert "не готова" in result


def test_remember_chroma_error(rag):
    rag.collection.add.side_effect = RuntimeError("boom")
    with patch.object(rag, "_get_embedding", return_value=[0.1]):
        result = rag.remember("привет", "привет")

    assert "Ошибка" in result


# --- get_stats / clear ---

def test_get_stats(rag):
    assert "5" in rag.get_stats()


def test_get_stats_not_ready(rag_not_ready):
    assert "не готова" in rag_not_ready.get_stats()


def test_clear(rag):
    assert "очищена" in rag.clear().lower()
    assert rag.client.delete_collection.called


def test_clear_not_ready(rag_not_ready):
    assert "не готова" in rag_not_ready.clear()


# --- check_ready ---

def test_check_ready_true(rag):
    assert rag.check_ready() is True


def test_check_ready_false(rag_not_ready):
    assert rag_not_ready.check_ready() is False


# --- search: живые ошибки мока ---

def test_search_no_embedding(rag):
    with patch.object(rag, "_get_embedding", return_value=None):
        result = rag.search("привет")
    assert "эмбеддинг" in result.lower()


def test_search_not_ready(rag_not_ready):
    assert "не готова" in rag_not_ready.search("привет")
