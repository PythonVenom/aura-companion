"""Calendar — Аура ведёт календарь.

Команды:
  «запиши клиента на 14:00 субботу»
  «что у меня на сегодня»
  «что на завтра»

Хранилище: ~/aura_private/CALENDAR.md

Наука: Duhigg 2012 (habit loop),
       Gollwitzer 1999 (implementation intentions).
"""
from __future__ import annotations

import contextlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse

CALENDAR_PATH = Path.home() / "aura_private" / "CALENDAR.md"


@dataclass
class Event:
    dt: datetime
    title: str
    done: bool = False

    def to_line(self) -> str:
        mark = "✅" if self.done else "⏳"
        return f"- {self.dt.strftime('%Y-%m-%d %H:%M')} | {mark} | {self.title}"


# ── Парсер дат ────────────────────────────────────────

WEEKDAYS = {
    "понедельник": 0, "вторник": 1, "среда": 2, "среду": 2,
    "четверг": 3, "пятница": 4, "пятницу": 4, "суббота": 5,
    "субботу": 5, "воскресенье": 6,
    "пн": 0, "вт": 1, "ср": 2, "чт": 3, "пт": 4, "сб": 5, "вс": 6,
}


def parse_when(text: str) -> datetime | None:
    """Парсит '14:00 субботу' → datetime."""
    text = text.lower()
    now = datetime.now()

    # Время
    m = re.search(r"(\d{1,2}):(\d{2})", text)
    if not m:
        m = re.search(r"в\s+(\d{1,2})\s*(?:час|ч|утра|дня|вечера)", text)
    hour, minute = (12, 0)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.lastindex and m.lastindex >= 2 else 0
        # вечер/день — 12+
        if any(w in text for w in ("вечера", "вечером", "дня", "днем")):
            hour = hour % 12 + 12 if hour < 12 else hour

    # День
    for name, wd in WEEKDAYS.items():
        # Word boundary: «вт» не должно ловиться в «завтра»
        if re.search(rf"\b{re.escape(name)}\b", text):
            days_ahead = (wd - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            target = (now + timedelta(days=days_ahead)).replace(
                hour=hour, minute=minute, second=0, microsecond=0,
            )
            return target

    # Точная дата «11 октября»
    months = {
        "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
        "мая": 5, "июня": 6, "июля": 7, "августа": 8,
        "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
    }
    m = re.search(r"(\d{1,2})\s+([а-я]+)", text)
    if m:
        day = int(m.group(1))
        month_name = m.group(2)
        if month_name in months:
            month = months[month_name]
            year = now.year if month >= now.month else now.year + 1
            try:
                return datetime(year, month, day, hour, minute)
            except ValueError:
                pass

    # «завтра», «послезавтра», «сегодня»
    if "завтра" in text:
        return (now + timedelta(days=1)).replace(
            hour=hour, minute=minute, second=0, microsecond=0,
        )
    if "послезавтра" in text:
        return (now + timedelta(days=2)).replace(
            hour=hour, minute=minute, second=0, microsecond=0,
        )
    if "сегодня" in text:
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    return None


# ── Чтение/запись ─────────────────────────────────────

def _ensure_file() -> None:
    CALENDAR_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CALENDAR_PATH.exists():
        CALENDAR_PATH.write_text(
            "# Календарь капитана\n\n"
            "Формат: `- YYYY-MM-DD HH:MM | ⏳/✅ | событие`\n\n",
            encoding="utf-8",
        )


def load_events() -> list[Event]:
    _ensure_file()
    events = []
    with contextlib.suppress(Exception):
        for line in CALENDAR_PATH.read_text(encoding="utf-8").splitlines():
            if not line.startswith("- "):
                continue
            parts = [p.strip() for p in line[2:].split("|")]
            if len(parts) < 3:
                continue
            try:
                dt = datetime.strptime(parts[0], "%Y-%m-%d %H:%M")
                done = "✅" in parts[1]
                events.append(Event(dt=dt, title=parts[2], done=done))
            except ValueError:
                continue
    return sorted(events, key=lambda e: e.dt)


def add_event(event: Event) -> None:
    _ensure_file()
    with CALENDAR_PATH.open("a", encoding="utf-8") as f:
        f.write(event.to_line() + "\n")


def events_for_day(target: datetime) -> list[Event]:
    return [
        e for e in load_events()
        if e.dt.date() == target.date() and not e.done
    ]


# ── Агент ─────────────────────────────────────────────

class AgentCalendar(MicroAgent):
    """Календарь — запись и чтение событий."""

    KEYWORDS = (
        "запиши", "напомни", "встреча", "клиент",
        "что у меня на сегодня", "что на завтра",
        "что в календаре",
    )

    def __init__(self):
        super().__init__("calendar", "Календарь капитана")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        if "запиши" in text or "напомни" in text:
            return True
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        text = request.text
        low = text.lower()

        # 1. «что на сегодня / завтра»
        if "сегодня" in low or "завтра" in low:
            target = datetime.now()
            if "завтра" in low:
                target = target + timedelta(days=1)
            events = events_for_day(target)
            day_name = "сегодня" if "сегодня" in low else "завтра"
            if not events:
                return AgentResponse.ok(
                    f"📅 На {day_name} — пусто",
                    self.name,
                )
            lines = [f"📅 На {day_name}:"]
            for e in events:
                lines.append(f"  {e.dt.strftime('%H:%M')} — {e.title}")
            return AgentResponse.ok("\n".join(lines), self.name)

        # 2. «запиши X на Y»
        if "запиши" in low or "напомни" in low:
            # Ищем дату и время
            when = parse_when(text)
            if when is None:
                return AgentResponse.ok(
                    "Когда напомнить? Скажи: 'в 14:00' или 'в субботу'.",
                    self.name,
                )

            # Убираем ключевые слова, время, дни недели → название
            title = text
            # Убираем служебные слова
            for kw in ("запиши", "напомни", "аура"):
                title = re.sub(rf"\b{kw}\b", "", title, flags=re.IGNORECASE)
            # Убираем время (14:00, 2:30)
            title = re.sub(r"\b\d{1,2}:\d{2}\b", "", title)
            # Убираем дни недели
            for wd in WEEKDAYS:
                title = re.sub(rf"\b{wd}\b", "", title, flags=re.IGNORECASE)
            # Убираем предлоги
            for kw in ("на", "в", "к"):
                title = re.sub(rf"\b{kw}\b", "", title, flags=re.IGNORECASE)
            # Убираем мусор
            title = re.sub(r"\s+", " ", title).strip(" ,.:;-").strip()
            if not title:
                title = "событие"

            event = Event(dt=when, title=title)
            add_event(event)

            return AgentResponse.ok(
                f"✅ Записала: {when.strftime('%d %B, %H:%M')} — {title}",
                self.name,
            )

        # 3. «что в календаре» — общий список
        events = load_events()
        upcoming = [e for e in events if not e.done and e.dt >= datetime.now()]
        if not upcoming:
            return AgentResponse.ok("📅 Календарь пуст", self.name)
        lines = ["📅 Ближайшие события:"]
        for e in upcoming[:5]:
            lines.append(f"  {e.dt.strftime('%d.%m %H:%M')} — {e.title}")
        return AgentResponse.ok("\n".join(lines), self.name)


__all__ = [
    "AgentCalendar", "Event",
    "add_event", "events_for_day", "load_events", "parse_when",
]
