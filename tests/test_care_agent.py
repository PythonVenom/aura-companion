"""Тесты CareAgent — напоминания (еда, вода, таблетки, сон)."""
from __future__ import annotations
from datetime import datetime, time as dtime
import pytest
from aura.agents.care import CareAgent, CareTask, should_trigger


def test_care_task_basic():
    t = CareTask(name="water", times=["10:00", "12:00"], message="Выпей воды")
    assert t.name == "water"
    assert len(t.times) == 2
    assert t.enabled is True


def test_should_trigger_match():
    task = CareTask(name="water", times=["14:00"], message="Вода")
    now = datetime(2026, 10, 2, 14, 0, 30)
    assert should_trigger(task, now) is True


def test_should_trigger_no_match():
    task = CareTask(name="water", times=["14:00"], message="Вода")
    now = datetime(2026, 10, 2, 15, 0, 0)
    assert should_trigger(task, now) is False


def test_should_trigger_disabled():
    task = CareTask(name="water", times=["14:00"], message="Вода", enabled=False)
    now = datetime(2026, 10, 2, 14, 0, 0)
    assert should_trigger(task, now) is False


def test_care_agent_init():
    a = CareAgent()
    assert a.name == "care"
    assert isinstance(a.tasks, list)


def test_care_agent_add_task():
    a = CareAgent()
    a.add_task("water", ["10:00"], "Выпей воды")
    assert len(a.tasks) == 1
    assert a.tasks[0].name == "water"


def test_care_agent_can_handle():
    from aura.core.protocol import AgentRequest
    a = CareAgent()
    assert a.can_handle(AgentRequest(text="аура, напомни пить воду"))
    assert a.can_handle(AgentRequest(text="какие напоминания"))
    assert not a.can_handle(AgentRequest(text="который час"))


def test_get_due_tasks():
    a = CareAgent()
    a.add_task("water", ["14:00"], "Вода")
    a.add_task("food", ["20:00"], "Еда")
    now = datetime(2026, 10, 2, 14, 0, 0)
    due = a.get_due_tasks(now)
    assert len(due) == 1
    assert due[0].name == "water"
