"""Тесты AgentMeds (GAPS #93).

Medication reminder (Czaja 2018).
"""
from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest

from aura.agents.meds import AgentMeds
from aura.core.protocol import AgentRequest


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def agent(tmp_path):
    """AgentMeds с временной БД (scheduler отключён)."""
    a = AgentMeds(start_scheduler=False)
    a.DB = tmp_path / "test_meds.db"
    a._init_db()
    return a


# ============================================================
# 1. Создание
# ============================================================
def test_agent_creation(agent):
    assert agent.name == "meds"


def test_scheduler_optional():
    """scheduler=False → нет потока."""
    a = AgentMeds(start_scheduler=False)
    assert a._scheduler is None


# ============================================================
# 2. can_handle
# ============================================================
@pytest.mark.parametrize("text", [
    "лекарство",
    "таблетки",
    "напомни про лекарство",
    "пора пить",
    "препарат",
])
def test_can_handle_positive(agent, text):
    assert agent.can_handle(AgentRequest(text=text))


@pytest.mark.parametrize("text", [
    "привет",
    "который час",
    "погода",
])
def test_can_handle_negative(agent, text):
    assert not agent.can_handle(AgentRequest(text=text))


# ============================================================
# 3. handle — not_handled
# ============================================================
def test_handle_not_handled(agent):
    r = _run(agent.handle(AgentRequest(text="привет")))
    assert r.text == "" or r.text is None


# ============================================================
# 4. Add medication
# ============================================================
def test_add_medication(agent):
    """Добавление лекарства + парсинг времени."""
    r = _run(agent.handle(AgentRequest(text="аура добавь лекарство аспирин в 08:00")))
    assert "аспирин" in r.text.lower()
    assert "08:00" in r.text

    # Проверяем БД
    conn = sqlite3.connect(agent.DB)
    rows = conn.execute("SELECT name, time_str FROM meds").fetchall()
    conn.close()
    assert len(rows) == 1
    assert "аспирин" in rows[0][0].lower()
    assert rows[0][1] == "08:00"


def test_add_no_time_uses_default(agent):
    """Без времени → 08:00."""
    r = _run(agent.handle(AgentRequest(text="добавь лекарство магний")))
    assert "08:00" in r.text


def test_add_empty_name(agent):
    """Пустое имя → подсказка."""
    r = _run(agent.handle(AgentRequest(text="добавь лекарство")))
    assert "Что за лекарство" in r.text


# ============================================================
# 5. List
# ============================================================
def test_list_empty(agent):
    r = _run(agent.handle(AgentRequest(text="список лекарств")))
    assert "пуст" in r.text.lower() or "пусто" in r.text.lower()


def test_list_with_items(agent):
    agent._add("аура добавь аспирин в 08:00")
    agent._add("аура добавь магний в 20:00")
    r = _run(agent.handle(AgentRequest(text="покажи лекарства")))
    assert "аспирин" in r.text.lower()
    assert "магний" in r.text.lower()


# ============================================================
# 6. Mark taken
# ============================================================
def test_mark_taken(agent):
    agent._add("аура добавь аспирин в 08:00")
    r = _run(agent.handle(AgentRequest(text="принял таблетки")))
    assert "принят" in r.text.lower()

    conn = sqlite3.connect(agent.DB)
    taken = conn.execute("SELECT taken FROM meds").fetchone()[0]
    conn.close()
    assert taken == 1


def test_status_after_taken(agent):
    agent._add("аура добавь аспирин в 08:00")
    agent._mark_taken()
    r = _run(agent.handle(AgentRequest(text="статус лекарств")))
    assert "принят" in r.text.lower()


# ============================================================
# 7. Visits
# ============================================================
def test_add_visit(agent):
    r = _run(agent.handle(AgentRequest(text="к врачу завтра в 15:00")))
    assert "врач" in r.text.lower() or "терапевт" in r.text.lower()
    assert "15:00" in r.text


def test_visit_with_doctor(agent):
    r = _run(agent.handle(AgentRequest(text="к стоматологу в 10:00")))
    assert "стоматолог" in r.text.lower()


def test_list_visits_empty(agent):
    r = _run(agent.handle(AgentRequest(text="покажи визиты")))
    assert "нет" in r.text.lower() or "визит" in r.text.lower()


def test_list_visits(agent):
    agent._add_visit("к терапевту в 10:00 завтра")
    r = _run(agent.handle(AgentRequest(text="покажи визиты")))
    assert "терапевт" in r.text.lower()


# ============================================================
# 8. Interactions
# ============================================================
def test_check_interactions_no_items(agent):
    r = _run(agent.handle(AgentRequest(text="проверь взаимодействия")))
    assert "не найдено" in r.text.lower()


def test_check_interactions_aspirin_warfarin(agent):
    """Аспирин + варфарин = кровотечение."""
    agent._add("аура добавь аспирин в 08:00")
    agent._add("аура добавь варфарин в 20:00")
    r = _run(agent.handle(AgentRequest(text="проверь взаимодействия лекарств")))
    assert "кровотечение" in r.text.lower() or "взаимодейств" in r.text.lower()


# ============================================================
# 9. Registry
# ============================================================
def test_meds_registered():
    from aura.bootstrap import build_orchestrator
    orch = build_orchestrator()
    names = set(orch.registry.list_names())
    assert "meds" in names
    assert "meds_offline" in names
