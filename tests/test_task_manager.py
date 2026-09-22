"""
Тесты для AgentTaskManager.

Работаем с временным файлом через monkeypatch.
"""

from __future__ import annotations

import pytest

from aura.agents.task_manager import AgentTaskManager
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def tm(tmp_path, monkeypatch):
    test_file = tmp_path / "tasks_test.json"
    monkeypatch.setattr(AgentTaskManager, "TASKS_FILE", str(test_file))
    return AgentTaskManager()


def test_init_empty(tm):
    assert tm.tasks == {}


def test_can_handle_add(tm):
    assert tm.can_handle(AgentRequest(text="добавь задачу купить хлеб"))


def test_can_handle_list(tm):
    assert tm.can_handle(AgentRequest(text="мои задачи"))


def test_can_handle_plan(tm):
    assert tm.can_handle(AgentRequest(text="план на сегодня"))


def test_cannot_handle_time(tm):
    assert not tm.can_handle(AgentRequest(text="который час"))


@pytest.mark.asyncio
async def test_handle_add(tm):
    resp = await tm.handle(AgentRequest(text="добавь задачу купить хлеб"))
    assert resp.status == AgentStatus.OK
    assert "Добавила" in resp.text
    assert "купить хлеб" in list(tm.tasks.values())[0]


@pytest.mark.asyncio
async def test_handle_add_empty(tm):
    resp = await tm.handle(AgentRequest(text="добавь задачу"))
    assert resp.status == AgentStatus.OK
    assert "Что добавить" in resp.text


@pytest.mark.asyncio
async def test_handle_list_empty(tm):
    resp = await tm.handle(AgentRequest(text="мои задачи"))
    assert resp.status == AgentStatus.OK
    assert "Задач нет" in resp.text


@pytest.mark.asyncio
async def test_handle_list_with_tasks(tm):
    tm.add_task("купить хлеб")
    tm.add_task("позвонить маме")
    resp = await tm.handle(AgentRequest(text="мои задачи"))
    assert "купить хлеб" in resp.text
    assert "позвонить маме" in resp.text


@pytest.mark.asyncio
async def test_handle_plan(tm):
    resp = await tm.handle(AgentRequest(text="план на сегодня"))
    assert resp.status == AgentStatus.OK
    assert "Задач нет" in resp.text


@pytest.mark.asyncio
async def test_handle_not_handled(tm):
    resp = await tm.handle(AgentRequest(text="просто болтовня"))
    assert resp.status == AgentStatus.NOT_HANDLED


def test_persistence(tmp_path, monkeypatch):
    test_file = tmp_path / "tasks2.json"
    monkeypatch.setattr(AgentTaskManager, "TASKS_FILE", str(test_file))
    t1 = AgentTaskManager()
    t1.add_task("тест")
    t2 = AgentTaskManager()
    assert "тест" in list(t2.tasks.values())
