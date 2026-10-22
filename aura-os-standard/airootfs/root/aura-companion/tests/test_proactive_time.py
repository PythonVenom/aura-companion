"""Bug 19: ProactiveEngine × TimeAgent + HealthAgent."""
import time
import pytest

from aura.agents import time_agent, health, proactive


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(time_agent, "TIMERS_PATH", tmp_path / "t.json")
    monkeypatch.setattr(health, "HEALTH_PATH", tmp_path / "h.json")
    monkeypatch.setattr(proactive, "STATE_PATH", tmp_path / "p.json")
    yield


def test_time_fired_condition_true(isolated):
    t = proactive.time_fired_trigger()
    # Добавили сработавший (fire_at в прошлом)
    time_agent.add_timer(-1, "тест")
    assert t.condition({}) is True


def test_time_fired_condition_false(isolated):
    t = proactive.time_fired_trigger()
    time_agent.add_timer(60, "будущее")
    assert t.condition({}) is False


def test_time_fired_action(isolated):
    t = proactive.time_fired_trigger()
    time_agent.add_timer(-1, "чай")
    assert t.condition({}) is True
    result = t.action()
    assert "⏰" in result
    assert "чай" in result
    # Кэш очищен
    assert t.action() == ""


def test_time_fired_no_double_fire(isolated):
    t = proactive.time_fired_trigger()
    time_agent.add_timer(-1, "чай")
    t.condition({})
    t.action()
    # Второй раз — уже ничего
    assert t.condition({}) is False


def test_health_due_condition(isolated):
    t = proactive.health_due_trigger()
    health.add_reminder("вода", every_minutes=0)
    time.sleep(0.05)
    assert t.condition({}) is True


def test_health_due_action(isolated):
    t = proactive.health_due_trigger()
    health.add_reminder("вода", every_minutes=0)
    time.sleep(0.05)
    t.condition({})
    result = t.action()
    assert "💊" in result


def test_health_due_no_pending(isolated):
    t = proactive.health_due_trigger()
    assert t.condition({}) is False


def test_default_engine_registers_both(isolated):
    engine = proactive.default_engine()
    names = [tr.name for tr in engine.triggers]
    assert "time_fired" in names
    assert "health_due" in names


def test_default_engine_priority(isolated):
    engine = proactive.default_engine()
    # time_fired должен быть выше health_due
    by_name = {tr.name: tr for tr in engine.triggers}
    assert by_name["time_fired"].priority > by_name["health_due"].priority
