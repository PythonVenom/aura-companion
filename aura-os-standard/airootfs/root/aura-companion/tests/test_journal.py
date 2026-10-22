"""
Тесты для AgentJournal.

Работаем с временным файлом в tmp_path — реальный JOURNAL.md не трогаем.
Никаких живых записей в историю проекта.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from aura.agents.journal import AgentJournal
from aura.core.protocol import AgentRequest, AgentStatus


# --- Фикстура: агент с временным файлом ---

@pytest.fixture
def journal(tmp_path, monkeypatch):
    """AgentJournal с временным JOURNAL.md."""
    test_file = tmp_path / "JOURNAL_TEST.md"

    # Подменяем путь на уровне экземпляра после создания
    with monkeypatch.context() as m:
        m.setattr(AgentJournal, "JOURNAL_FILE", str(test_file))
        j = AgentJournal()
    return j


@pytest.fixture
def journal_with_entries(journal):
    """Журнал с уже записанными данными."""
    journal.log_dialog("сколько времени", "6 часов вечера")
    journal.add_task("купить молоко")
    journal.add_task("позвонить маме")
    return journal


# --- can_handle ---

def test_can_handle_show(journal):
    assert journal.can_handle(AgentRequest(text="покажи журнал"))


def test_can_handle_what_i_did(journal):
    assert journal.can_handle(AgentRequest(text="что я делал"))


def test_can_handle_pending(journal):
    assert journal.can_handle(AgentRequest(text="что осталось"))


def test_can_handle_add(journal):
    assert journal.can_handle(AgentRequest(text="добавь задачу купить хлеб"))


def test_can_handle_close(journal):
    assert journal.can_handle(AgentRequest(text="закрой задачу купить хлеб"))


def test_can_handle_stats(journal):
    assert journal.can_handle(AgentRequest(text="статистика журнала"))


def test_cannot_handle_unrelated(journal):
    assert not journal.can_handle(AgentRequest(text="который час"))


def test_cannot_handle_empty(journal):
    assert not journal.can_handle(AgentRequest(text=""))


# --- log_dialog ---

def test_log_dialog_creates_entry(journal):
    result = journal.log_dialog("привет", "привет, Создатель")

    assert "Записала" in result
    content = Path(journal.journal_file).read_text(encoding="utf-8")
    assert "### " in content
    assert "привет" in content


def test_log_dialog_truncates_long_text(journal):
    long_user = "а" * 500
    long_aura = "б" * 500
    journal.log_dialog(long_user, long_aura)

    content = Path(journal.journal_file).read_text(encoding="utf-8")
    # user_short = 100 символов, aura_short = 150
    assert "а" * 100 in content
    assert "а" * 500 not in content
    assert "б" * 150 in content
    assert "б" * 500 not in content


# --- add_task / close_task ---

def test_add_task(journal):
    result = journal.add_task("купить молоко")

    assert "Добавила" in result
    assert "купить молоко" in journal.get_pending_tasks()


def test_close_task(journal):
    journal.add_task("купить молоко")
    result = journal.close_task("купить молоко")

    assert "закрыта" in result.lower()
    assert "купить молоко" not in journal.get_pending_tasks()
    assert "купить молоко" in journal.get_done_tasks()


def test_close_task_not_found(journal):
    result = journal.close_task("несуществующая задача")
    assert "не найдена" in result.lower()


# --- get_last_session ---

def test_get_last_session_after_dialog(journal):
    journal.log_dialog("тест", "ответ")
    session = journal.get_last_session()

    assert session is not None
    assert session["is_today"] is True
    assert "date" in session
    assert "time" in session


def test_get_last_session_empty_file(journal):
    # Файл только с шапкой, без дат
    session = journal.get_last_session()
    assert session is None or session.get("date") is None


# --- show_pending ---

def test_show_pending_with_tasks(journal_with_entries):
    result = journal_with_entries.show_pending()
    assert "купить молоко" in result
    assert "позвонить маме" in result


def test_show_pending_empty(journal):
    result = journal.show_pending()
    assert "нет" in result.lower()


# --- handle: команды ---

@pytest.mark.asyncio
async def test_handle_show_journal(journal_with_entries):
    resp = await journal_with_entries.handle(AgentRequest(text="покажи журнал"))

    assert resp.status == AgentStatus.OK
    assert resp.agent_name == "journal"


@pytest.mark.asyncio
async def test_handle_pending(journal_with_entries):
    resp = await journal_with_entries.handle(AgentRequest(text="что осталось"))

    assert resp.status == AgentStatus.OK
    assert "купить молоко" in resp.text


@pytest.mark.asyncio
async def test_handle_add_task(journal):
    resp = await journal.handle(AgentRequest(text="добавь задачу позвонить в банк"))

    assert resp.status == AgentStatus.OK
    assert "позвонить в банк" in journal.get_pending_tasks()


@pytest.mark.asyncio
async def test_handle_add_task_empty(journal):
    resp = await journal.handle(AgentRequest(text="добавь задачу"))

    assert resp.status == AgentStatus.OK
    assert "Что добавить" in resp.text


@pytest.mark.asyncio
async def test_handle_close_task(journal_with_entries):
    resp = await journal_with_entries.handle(
        AgentRequest(text="закрой задачу купить молоко")
    )

    assert resp.status == AgentStatus.OK
    assert "купить молоко" not in journal_with_entries.get_pending_tasks()


@pytest.mark.asyncio
async def test_handle_stats(journal_with_entries):
    resp = await journal_with_entries.handle(AgentRequest(text="статистика журнала"))

    assert resp.status == AgentStatus.OK
    assert "осталось" in resp.text.lower() or "сделано" in resp.text.lower()


@pytest.mark.asyncio
async def test_handle_not_handled(journal):
    resp = await journal.handle(AgentRequest(text="просто болтовня"))

    assert resp.status == AgentStatus.NOT_HANDLED


# --- _ensure_file ---

def test_ensure_file_creates_header(tmp_path, monkeypatch):
    test_file = tmp_path / "NEW_JOURNAL.md"
    monkeypatch.setattr(AgentJournal, "JOURNAL_FILE", str(test_file))
    j = AgentJournal()

    content = test_file.read_text(encoding="utf-8")
    assert "# 📔 Журнал Ауры" in content
