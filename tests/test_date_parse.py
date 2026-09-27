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
