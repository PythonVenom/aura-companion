"""ChatSense ph.6: unanswered_messages_trigger сохраняет события в календарь."""

from unittest.mock import MagicMock
from aura.agents import chat_sense


def test_trigger_saves_events(tmp_path, monkeypatch):
    from aura.agents.proactive import unanswered_messages_trigger
    monkeypatch.setattr(chat_sense, "CALENDAR_PATH", tmp_path / "cal.json")
    monkeypatch.setattr(chat_sense, "STATE_PATH", tmp_path / "state.json")

    m = MagicMock()
    m.get_all_previews.return_value = [
        {"chat": "Аня", "preview": "завтра в 14:00 массаж у Ивана"},
        {"chat": "Борис", "preview": "привет"},
    ]
    def get_agent(name):
        return m if name == "messenger" else None

    t = unanswered_messages_trigger(get_agent)
    state = {}
    t.condition(state)
    t.action()

    cal = chat_sense.load_calendar()
    assert len(cal) == 1
    assert cal[0]["chat"] == "Аня"
    assert "массаж" in cal[0]["text"]


def test_trigger_no_events_no_save(tmp_path, monkeypatch):
    from aura.agents.proactive import unanswered_messages_trigger
    monkeypatch.setattr(chat_sense, "CALENDAR_PATH", tmp_path / "cal.json")
    monkeypatch.setattr(chat_sense, "STATE_PATH", tmp_path / "state.json")

    m = MagicMock()
    m.get_all_previews.return_value = [
        {"chat": "Борис", "preview": "привет"},
    ]
    def get_agent(name):
        return m if name == "messenger" else None

    t = unanswered_messages_trigger(get_agent)
    state = {}
    t.condition(state)

    assert chat_sense.load_calendar() == []
