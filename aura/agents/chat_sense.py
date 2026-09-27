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


# === ph.4: календарь ===
CALENDAR_PATH = Path("/tmp/aura_calendar.json")
PURGE_DAYS = 3   # удаляем события старше 3 дней


def load_calendar() -> list:
    if not CALENDAR_PATH.exists():
        return []
    try:
        return json.loads(CALENDAR_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_calendar(items: list) -> None:
    try:
        CALENDAR_PATH.write_text(
            json.dumps(items, ensure_ascii=False, indent=2),
            encoding="utf-8")
    except Exception:
        pass


def save_event(event: dict) -> None:
    """Сохранить событие. Дубликаты (when+chat+text) — пропускаем."""
    if not event or not event.get("when"):
        return
    items = load_calendar()
    key = (event.get("when"), event.get("chat"), event.get("text"))
    for e in items:
        if (e.get("when"), e.get("chat"), e.get("text")) == key:
            return
    items.append(event)
    _save_calendar(items)


def get_today(now: datetime | None = None) -> list:
    if now is None:
        now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    items = load_calendar()
    out = [e for e in items if e.get("when", "").startswith(today_str)]
    out.sort(key=lambda e: e.get("when", ""))
    return out


def purge_old(now: datetime | None = None) -> None:
    if now is None:
        now = datetime.now()
    cutoff = now - timedelta(days=PURGE_DAYS)
    cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M")
    items = load_calendar()
    fresh = [e for e in items if e.get("when", "") >= cutoff_str]
    if len(fresh) != len(items):
        _save_calendar(fresh)


def summary_day(now: datetime | None = None) -> str:
    """Комбинированная сводка: события сегодня. Позже — + неотвеченные."""
    today = summary_today(now=now)
    if today:
        return today
    return ""


def summary_tomorrow(now: datetime | None = None) -> str:
    """Голосовая сводка событий на завтра."""
    if now is None:
        now = datetime.now()
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    items = load_calendar()
    tomorrow_items = [e for e in items if e.get("when", "").startswith(tomorrow)]
    tomorrow_items.sort(key=lambda e: e.get("when", ""))
    if not tomorrow_items:
        return ""
    parts = []
    for e in tomorrow_items:
        t = e.get("when", "")[11:16]
        chat = e.get("chat", "").split()[0]
        text = e.get("text", "")[:60]
        parts.append(f"{t} — {chat}: {text}")
    return "Завтра: " + ". ".join(parts)


def export_ics(now: datetime | None = None) -> str:
    """Экспорт календаря в формат iCalendar (.ics)."""
    if now is None:
        now = datetime.now()
    items = load_calendar()
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Aura//Aura Calendar//RU",
    ]
    for e in items:
        when = e.get("when", "")
        if not when:
            continue
        # 2026-09-28T14:00 → 20260928T140000
        try:
            dt = datetime.strptime(when, "%Y-%m-%dT%H:%M")
            start = dt.strftime("%Y%m%dT%H%M%S")
            end = (dt + timedelta(hours=1)).strftime("%Y%m%dT%H%M%S")
        except Exception:
            continue
        summary = f"{e.get('chat', '')}: {e.get('text', '')}"[:80]
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{when.replace(':', '').replace('-', '')}@aura",
            f"DTSTART:{start}",
            f"DTEND:{end}",
            f"SUMMARY:{summary}",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    return "\n".join(lines)


def summary_today(now: datetime | None = None) -> str:
    """Голосовая сводка: «14:00 — Аня: массаж у Ивана. 18:00 — Борис: встреча.»"""
    today = get_today(now=now)
    if not today:
        return ""
    parts = []
    for e in today:
        t = e.get("when", "")[11:16]
        chat = e.get("chat", "").split()[0]
        text = e.get("text", "")[:60]
        parts.append(f"{t} — {chat}: {text}")
    return "Сегодня: " + ". ".join(parts)


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


_TRIGGERS = (
    "встреча", "встречу", "встретиться",
    "массаж", "массажа",
    "позвони", "позвонить", "созвон", "созвонимся",
    "напомни", "напомнить",
    "приём", "прием", "приёма",
    "запиши", "записать",
    "приходи", "заходи", "подъезжай",
)


def extract_events(previews: list, now: datetime | None = None) -> list:
    """Найти события в чатах (встреча/массаж/позвони + дата).

    Возвращает [{'when': 'YYYY-MM-DDTHH:MM', 'chat', 'text', 'trigger'}].
    Пропускает «Вы:» и сообщения без триггера.
    """
    if now is None:
        now = datetime.now()
    out = []
    for p in previews:
        chat = (p.get("chat") or p.get("name") or "").strip()
        prev = p.get("preview", "").strip()
        if not chat or not prev:
            continue
        if prev.startswith("Вы:"):
            continue
        low = prev.lower()
        trigger = next((t for t in _TRIGGERS if t in low), "")
        if not trigger:
            continue
        when = parse_date_ru(prev, now=now)
        if when is None:
            continue
        out.append({
            "when": when.strftime("%Y-%m-%dT%H:%M"),
            "chat": chat,
            "text": prev,
            "trigger": trigger,
        })
    return out


_ACTIONS = {
    "call": ("позвони", "позвонить", "набери", "созвонись"),
    "meet": ("встреча", "встречу", "встретиться", "увидимся"),
    "remind": ("напомни", "напомнить", "не забудь"),
    "pay": ("оплати", "оплатить", "заплати", "переведи"),
}


def parse_action_ru(text: str, now: datetime | None = None) -> dict | None:
    """Извлечь действие из текста (для чатов).

    Возвращает {'action', 'target', 'when', 'text'} или None.
    """
    import re
    if not text:
        return None
    if now is None:
        now = datetime.now()
    low = text.lower().strip()

    # Определить действие
    action = None
    trigger_word = ""
    for act, words in _ACTIONS.items():
        for w in words:
            if w in low:
                action = act
                trigger_word = w
                break
        if action:
            break

    if not action:
        return None

    # Целевой объект — после триггера
    idx = low.index(trigger_word) + len(trigger_word)
    rest = text[idx:].strip(" .,!?:;")

    # Отрезаем временную часть
    time_m = re.search(r"\s+в\s+\d{1,2}:?\d{0,2}", rest)
    target = rest
    if time_m:
        target = rest[:time_m.start()].strip()
    elif " завтра" in rest:
        target = rest.split(" завтра")[0].strip()
    elif " сегодня" in rest:
        target = rest.split(" сегодня")[0].strip()

    # Отрезаем «до X»
    if " до " in target:
        target = target.split(" до ")[0].strip()

    # Парсим дату
    when = parse_date_ru(text, now=now)
    when_str = when.strftime("%Y-%m-%dT%H:%M") if when else ""

    return {
        "action": action,
        "target": target[:60],
        "when": when_str,
        "text": text[:120],
    }


def prioritize(items: list, vip: list | None = None) -> list:
    """Сортировка: VIP-чаты в начале, остальные по порядку."""
    if not vip:
        return list(items)
    vip_lower = [v.lower() for v in vip]
    vip_items = []
    other_items = []
    for it in items:
        chat = (it.get("chat") or "").lower()
        if any(v in chat for v in vip_lower):
            vip_items.append(it)
        else:
            other_items.append(it)
    return vip_items + other_items


def find_unanswered(previews: list) -> list:
    """previews: [{'chat':..., 'preview':...}].

    Возвращает список неотвеченных:
    [{'chat':..., 'preview':..., 'reason':'unanswered'}]

    «Неотвеченное» = preview НЕ начинается с «Вы:» и не пуст.
    """
    out = []
    for p in previews:
        # Bridge отдаёт "name", наш код — "chat". Поддерживаем оба.
        chat = (p.get("chat") or p.get("name") or "").strip()
        prev = p.get("preview", "").strip()
        if not chat or not prev:
            continue
        if prev.startswith("Вы:"):
            continue
        _sys = ("коды подтверждения", "max на iphone", "аура")
        if any(x in chat.lower() for x in _sys):
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
    "summary", "parse_date_ru", "extract_events", "save_event", "load_calendar", "get_today", "summary_today", "purge_old", "CALENDAR_PATH", "STATE_PATH", "RE_MIND_TTL",
]
