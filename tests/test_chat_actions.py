"""ChatSense: парсинг действий из чатов (call, meet, pay, remind)."""
from datetime import datetime

from aura.agents.chat_sense import parse_action_ru


def test_parse_call():
    now = datetime(2026, 9, 28, 12, 0)
    r = parse_action_ru("позвони маме в 18:00", now=now)
    assert r is not None
    assert r["action"] == "call"
    assert "маме" in r["target"]


def test_parse_meet():
    now = datetime(2026, 9, 28, 12, 0)
    r = parse_action_ru("встреча с Иваном завтра в 14:00", now=now)
    assert r is not None
    assert r["action"] == "meet"


def test_parse_pay():
    now = datetime(2026, 9, 28, 12, 0)
    r = parse_action_ru("оплати квартиру до 10 октября", now=now)
    assert r is not None
    assert r["action"] == "pay"


def test_parse_no_action():
    r = parse_action_ru("привет как дела")
    assert r is None
