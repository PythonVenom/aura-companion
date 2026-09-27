"""Покрытие всех триггеров ProactiveEngine."""
from aura.agents.proactive import (
    Trigger, ProactiveEngine, default_engine,
    morning_briefing_trigger, max_new_message_trigger,
    unanswered_messages_trigger, calendar_reminder_trigger,
    morning_checklist_trigger, upcoming_calendar_trigger,
)


def test_default_engine_has_6_triggers():
    e = default_engine(get_agent=None)
    assert len(e.triggers) >= 5


def test_all_triggers_have_priority():
    e = default_engine(get_agent=None)
    for t in e.triggers:
        assert hasattr(t, "priority")
        assert t.priority > 0


def test_all_triggers_have_cooldown():
    e = default_engine(get_agent=None)
    for t in e.triggers:
        assert t.cooldown_sec >= 0


def test_morning_briefing_returns_trigger():
    t = morning_briefing_trigger(get_agent=None)
    assert t.name == "morning_briefing"


def test_unanswered_messages_returns_trigger():
    t = unanswered_messages_trigger(get_agent=None)
    assert t.name == "unanswered_messages"


def test_calendar_reminder_returns_trigger():
    t = calendar_reminder_trigger(get_agent=None)
    assert t.name == "calendar_reminder"


def test_morning_checklist_returns_trigger():
    t = morning_checklist_trigger(get_agent=None)
    assert t.name == "morning_checklist"


def test_upcoming_calendar_returns_trigger():
    t = upcoming_calendar_trigger(get_agent=None)
    assert t.name == "upcoming_calendar"
