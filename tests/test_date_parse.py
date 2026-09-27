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


# === ph.4: календарь (JSON storage) ===

def test_save_event(tmp_path, monkeypatch):
    from aura.agents import chat_sense
    monkeypatch.setattr(chat_sense, "CALENDAR_PATH", tmp_path / "cal.json")
    chat_sense.save_event({
        "when": "2026-09-28T14:00",
        "chat": "Аня",
        "text": "завтра в 14:00 массаж",
        "trigger": "массаж",
    })
    assert (tmp_path / "cal.json").exists()


def test_save_event_dedup(tmp_path, monkeypatch):
    """Одно и то же событие не дублируется."""
    from aura.agents import chat_sense
    monkeypatch.setattr(chat_sense, "CALENDAR_PATH", tmp_path / "cal.json")
    e = {"when": "2026-09-28T14:00", "chat": "Аня",
         "text": "завтра в 14:00 массаж", "trigger": "массаж"}
    chat_sense.save_event(e)
    chat_sense.save_event(e)
    assert len(chat_sense.load_calendar()) == 1


def test_get_today(tmp_path, monkeypatch):
    from aura.agents import chat_sense
    from datetime import datetime as dt
    monkeypatch.setattr(chat_sense, "CALENDAR_PATH", tmp_path / "cal.json")
    chat_sense.save_event({"when": "2026-09-28T14:00", "chat": "Аня",
                           "text": "массаж", "trigger": "массаж"})
    chat_sense.save_event({"when": "2026-09-28T18:00", "chat": "Борис",
                           "text": "встреча", "trigger": "встреча"})
    chat_sense.save_event({"when": "2026-09-29T10:00", "chat": "Вера",
                           "text": "приём", "trigger": "приём"})
    today = chat_sense.get_today(now=dt(2026, 9, 28, 8, 0))
    assert len(today) == 2


def test_summary_today(tmp_path, monkeypatch):
    from aura.agents import chat_sense
    from datetime import datetime as dt
    monkeypatch.setattr(chat_sense, "CALENDAR_PATH", tmp_path / "cal.json")
    chat_sense.save_event({"when": "2026-09-28T14:00", "chat": "Аня",
                           "text": "массаж у Ивана", "trigger": "массаж"})
    s = chat_sense.summary_today(now=dt(2026, 9, 28, 8, 0))
    assert "14:00" in s
    assert "Аня" in s


def test_summary_today_empty(tmp_path, monkeypatch):
    from aura.agents import chat_sense
    from datetime import datetime as dt
    monkeypatch.setattr(chat_sense, "CALENDAR_PATH", tmp_path / "cal.json")
    assert chat_sense.summary_today(now=dt(2026, 9, 28, 8, 0)) == ""


def test_purge_old(tmp_path, monkeypatch):
    """Старые события (3+ дня) удаляются."""
    from aura.agents import chat_sense
    from datetime import datetime as dt
    monkeypatch.setattr(chat_sense, "CALENDAR_PATH", tmp_path / "cal.json")
    chat_sense.save_event({"when": "2026-09-20T14:00", "chat": "Аня",
                           "text": "старое", "trigger": "массаж"})
    chat_sense.save_event({"when": "2026-09-28T14:00", "chat": "Аня",
                           "text": "новое", "trigger": "массаж"})
    chat_sense.purge_old(now=dt(2026, 9, 28, 8, 0))
    assert len(chat_sense.load_calendar()) == 1


# === ph.7: новые триггеры ===

def test_extract_phone_call():
    from aura.agents.chat_sense import extract_events
    from datetime import datetime as dt
    now = dt(2026, 9, 27, 12, 0)
    events = extract_events([
        {"chat": "Мама", "preview": "позвони мне в 18:00"}
    ], now=now)
    assert len(events) == 1
    assert events[0]["trigger"] == "позвони"
    assert "18:00" in events[0]["when"]


def test_extract_meeting_tomorrow():
    from aura.agents.chat_sense import extract_events
    from datetime import datetime as dt
    now = dt(2026, 9, 27, 12, 0)
    events = extract_events([
        {"chat": "Борис", "preview": "завтра встреча в 10:00"}
    ], now=now)
    assert len(events) == 1
    assert events[0]["when"].startswith("2026-09-28T10:00")


def test_extract_no_date_no_event():
    """Триггер есть, даты нет — событие не создаём."""
    from aura.agents.chat_sense import extract_events
    events = extract_events([
        {"chat": "Мама", "preview": "позвони когда сможешь"}
    ])
    assert events == []


def test_summary_tomorrow(tmp_path, monkeypatch):
    """Сводка событий на завтра."""
    from aura.agents import chat_sense
    from datetime import datetime as dt, timedelta
    monkeypatch.setattr(chat_sense, "CALENDAR_PATH", tmp_path / "cal.json")
    tomorrow = dt.now() + timedelta(days=1)
    chat_sense.save_event({
        "when": tomorrow.strftime("%Y-%m-%dT14:00"),
        "chat": "Аня",
        "text": "массаж",
        "trigger": "массаж",
    })
    s = chat_sense.summary_tomorrow()
    assert "Аня" in s or "14:00" in s


def test_ics_export(tmp_path, monkeypatch):
    """Экспорт календаря в .ics."""
    from aura.agents import chat_sense
    from datetime import datetime as dt
    monkeypatch.setattr(chat_sense, "CALENDAR_PATH", tmp_path / "cal.json")
    chat_sense.save_event({
        "when": "2026-09-28T14:00",
        "chat": "Аня",
        "text": "массаж у Ивана",
        "trigger": "массаж",
    })
    ics = chat_sense.export_ics()
    assert "BEGIN:VCALENDAR" in ics
    assert "BEGIN:VEVENT" in ics
    assert "2026-09-28" in ics or "20260928" in ics
