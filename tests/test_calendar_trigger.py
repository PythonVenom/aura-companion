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
