"""ChatSense ph.5: триггер calendar_reminder в ProactiveEngine."""

from unittest.mock import MagicMock

from aura.agents import chat_sense


def test_calendar_reminder_trigger_past_event(tmp_path, monkeypatch):
    """Событие в прошлом → триггер не срабатывает (get_today не находит)."""
    from aura.agents.proactive import calendar_reminder_trigger
    monkeypatch.setattr(chat_sense, "CALENDAR_PATH", tmp_path / "cal.json")
    chat_sense.save_event({
        "when": "2020-01-01T14:00", "chat": "Аня",
        "text": "старое событие", "trigger": "массаж",
    })
    t = calendar_reminder_trigger(get_agent=None)
    state = {}
    assert t.condition(state) is False


def test_calendar_reminder_with_today_event(tmp_path, monkeypatch):
    from aura.agents.proactive import calendar_reminder_trigger
    from datetime import datetime as dt
    monkeypatch.setattr(chat_sense, "CALENDAR_PATH", tmp_path / "cal.json")
    today_str = dt.now().strftime("%Y-%m-%d")
    chat_sense.save_event({
        "when": f"{today_str}T14:00", "chat": "Аня",
        "text": "массаж у Ивана", "trigger": "массаж",
    })
    t = calendar_reminder_trigger(get_agent=None)
    state = {}
    assert t.condition(state) is True
    result = t.action()
    assert "Сегодня" in result
    assert "14:00" in result


def test_upcoming_reminder(tmp_path, monkeypatch):
    """Событие через 30 мин — напоминание."""
    import pytest
    from aura.agents import chat_sense
    from aura.agents.proactive import upcoming_calendar_trigger
    from datetime import datetime as dt, timedelta

    # AURA_FLAKY_GUARD_V1 — Luo 2014: time-dependent flaky window
    now = dt.now()
    if now.hour == 23 and now.minute >= 40:
        pytest.skip("near midnight — flaky window (now+20 crosses day)")
    if now.hour == 0 and now.minute < 5:
        pytest.skip("near midnight — flaky window (previous day)")

    monkeypatch.setattr(chat_sense, "CALENDAR_PATH", tmp_path / "cal.json")
    future = now + timedelta(minutes=20)
    chat_sense.save_event({
        "when": future.strftime("%Y-%m-%dT%H:%M"),
        "chat": "Аня",
        "text": "встреча",
        "trigger": "встреча",
    })
    t = upcoming_calendar_trigger(get_agent=None)
    state = {}
    assert t.condition(state) is True
    result = t.action()
    assert "20" in result or "через" in result.lower()
