"""ChatSense ph.2: парсинг русских дат из чатов."""
from datetime import datetime, timedelta

from aura.agents.chat_sense import parse_date_ru


def test_today():
    now = datetime(2026, 9, 27, 12, 0)
    r = parse_date_ru("сегодня в 15:00", now=now)
    assert r == datetime(2026, 9, 27, 15, 0)


def test_tomorrow():
    now = datetime(2026, 9, 27, 12, 0)
    r = parse_date_ru("завтра в 10:30", now=now)
    assert r == datetime(2026, 9, 28, 10, 30)


def test_weekday():
    now = datetime(2026, 9, 27, 12, 0)  # воскресенье
    r = parse_date_ru("в пятницу в 14:00", now=now)
    assert r == datetime(2026, 10, 2, 14, 0)


def test_date_only():
    now = datetime(2026, 9, 27, 12, 0)
    r = parse_date_ru("15 октября", now=now)
    assert r == datetime(2026, 10, 15)


def test_no_date_returns_none():
    assert parse_date_ru("привет как дела") is None


def test_time_only():
    now = datetime(2026, 9, 27, 12, 0)
    r = parse_date_ru("в 18:00", now=now)
    assert r == datetime(2026, 9, 27, 18, 0)


# === ph.3: детектор событий ===

def test_extract_event_with_trigger():
    """«завтра в 14:00 массаж» → event с датой и триггером."""
    from aura.agents.chat_sense import extract_events
    now = datetime(2026, 9, 27, 12, 0)
    events = extract_events([
        {"chat": "Аня", "preview": "завтра в 14:00 массаж у Ивана"}
    ], now=now)
    assert len(events) == 1
    e = events[0]
    assert e["when"] == "2026-09-28T14:00"
    assert e["chat"] == "Аня"
    assert "массаж" in e["text"].lower()


def test_extract_event_meeting():
    from aura.agents.chat_sense import extract_events
    now = datetime(2026, 9, 27, 12, 0)
    events = extract_events([
        {"chat": "Борис", "preview": "встреча в пятницу в 10:00"}
    ], now=now)
    assert len(events) == 1
    assert events[0]["when"].startswith("2026-10-02T10:00")


def test_extract_no_trigger_skipped():
    """Нет триггера — не событие."""
    from aura.agents.chat_sense import extract_events
    events = extract_events([
        {"chat": "Аня", "preview": "завтра в 14:00 погода хорошая"}
    ])
    assert events == []


def test_extract_my_message_skipped():
    from aura.agents.chat_sense import extract_events
    events = extract_events([
        {"chat": "Аня", "preview": "Вы: завтра в 14:00 встреча"}
    ])
    assert events == []
