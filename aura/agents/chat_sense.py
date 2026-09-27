"""Bug 16: ChatSense — смысл чатов + напоминания.

MVP:
- Найти неотвеченные сообщения (последнее — от собеседника)
- Напомнить раз в N часов
- Формат: «Тебе не ответили: <чат> — с <время>»

Phase 2:
- Календарь из чатов (ADR-015)
- Смысловые события
"""
from __future__ import annotations
from datetime import datetime, timedelta

import json
import time
from pathlib import Path


STATE_PATH = Path("/tmp/aura_chat_sense.json")
RE_MIND_TTL = 4 * 3600   # не напоминать чаще 4 часов про один чат


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {"reminded": {}}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"reminded": {}}


def _save_state(state: dict) -> None:
    try:
        STATE_PATH.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


_WEEKDAYS = {
    "понедельник": 0, "понедельнику": 0,
    "вторник": 1, "вторнику": 1,
    "среду": 2, "среда": 2, "среде": 2,
    "четверг": 3, "четвергу": 3,
    "пятницу": 4, "пятница": 4, "пятнице": 4,
    "субботу": 5, "суббота": 5, "субботе": 5,
    "воскресенье": 6, "воскресенью": 6,
}

_MONTHS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
    "мая": 5, "июня": 6, "июля": 7, "августа": 8,
    "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}


def parse_date_ru(text: str, now: datetime | None = None):
    """Извлечь дату/время из русской фразы. None если не найдено.

    Поддерживает:
    - «сегодня в 15:00», «завтра в 10:30»
    - «в пятницу в 14:00»
    - «15 октября»
    - «в 18:00»
    """
    import re
    if not text:
        return None
    if now is None:
        now = datetime.now()
    t = text.lower().strip()

    # Часы:минуты
    time_m = re.search(r"\b(\d{1,2}):(\d{2})\b", t)
    hour = minute = None
    if time_m:
        hour, minute = int(time_m.group(1)), int(time_m.group(2))

    # Час без минут: «в 15 ч»
    if hour is None:
        hm = re.search(r"\bв\s+(\d{1,2})\s*(?:ч|час)", t)
        if hm:
            hour, minute = int(hm.group(1)), 0

    base_date = None

    if "сегодня" in t:
        base_date = now.date()
    elif "завтра" in t:
        base_date = (now + timedelta(days=1)).date()
    elif "послезавтра" in t:
        base_date = (now + timedelta(days=2)).date()
    else:
        # День недели
        for wd_name, wd_num in _WEEKDAYS.items():
            if wd_name in t:
                days_ahead = (wd_num - now.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                base_date = (now + timedelta(days=days_ahead)).date()
                break

    # Дата «15 октября»
    if base_date is None:
        dm = re.search(r"\b(\d{1,2})\s+([а-яё]+)", t)
        if dm:
            day = int(dm.group(1))
            month_name = dm.group(2)
            if month_name in _MONTHS and 1 <= day <= 31:
                month = _MONTHS[month_name]
                year = now.year
                if month < now.month:
                    year += 1
                base_date = datetime(year, month, day).date()

    if base_date is None and hour is None:
        return None

    if base_date is None:
        base_date = now.date()

    if hour is None:
        return datetime(base_date.year, base_date.month, base_date.day)

    return datetime(base_date.year, base_date.month, base_date.day, hour, minute or 0)


def find_unanswered(previews: list) -> list:
    """previews: [{'chat':..., 'preview':...}].

    Возвращает список неотвеченных:
    [{'chat':..., 'preview':..., 'reason':'unanswered'}]

    «Неотвеченное» = preview НЕ начинается с «Вы:» и не пуст.
    """
    out = []
    for p in previews:
        chat = p.get("chat", "").strip()
        prev = p.get("preview", "").strip()
        if not chat or not prev:
            continue
        if prev.startswith("Вы:"):
            continue
        # Системные/инфо-чаты
        if any(x in chat.lower() for x in ("коды подтверждения", "max на iphone")):
            continue
        out.append({"chat": chat, "preview": prev, "reason": "unanswered"})
    return out


def filter_by_reminder_ttl(items: list, state: dict | None = None) -> list:
    """Убрать те, о которых недавно напоминали."""
    if state is None:
        state = _load_state()
    reminded = state.get("reminded", {})
    now = time.time()
    out = []
    for it in items:
        chat = it["chat"]
        last = reminded.get(chat, 0)
        if now - last < RE_MIND_TTL:
            continue
        out.append(it)
    return out


def mark_reminded(items: list) -> None:
    state = _load_state()
    now = time.time()
    for it in items:
        state.setdefault("reminded", {})[it["chat"]] = now
    _save_state(state)


def summary(items: list) -> str:
    """Короткий текст для голоса."""
    if not items:
        return ""
    if len(items) == 1:
        return f"Тебе не ответили: {items[0]['chat']}"
    return f"Тебе не ответили в {len(items)} чатах. Первый — {items[0]['chat']}"


__all__ = [
    "find_unanswered", "filter_by_reminder_ttl", "mark_reminded",
    "summary", "parse_date_ru", "STATE_PATH", "RE_MIND_TTL",
]
