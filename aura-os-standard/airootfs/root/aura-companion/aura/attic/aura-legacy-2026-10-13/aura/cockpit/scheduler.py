"""Scheduler — время и события корабля.

Определяет, какое приветствие сказать, и стоит ли вообще говорить.
Триггер: разница между last_seen и now > min_gap_minutes.

Наука: Duhigg 2012 (habit loop — триггер по времени),
       Nielsen 1993 (visibility — Аура замечает, что ты пришёл).
"""

from __future__ import annotations

from datetime import UTC, datetime


def greeting_event(hour: int) -> str:
    """Какое приветствие по часу суток (0-23).

    05-11 → morning, 12-17 → day, 18-22 → evening, 23-04 → night.
    """
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 18:
        return "day"
    if 18 <= hour < 23:
        return "evening"
    return "night"


def should_greet(
    last_seen_iso: str,
    now: datetime | None = None,
    min_gap_minutes: int = 360,
) -> bool:
    """Стоит ли приветствовать.

    True, если прошло > min_gap_minutes с последнего визита.
    По умолчанию 6 часов — «утро после сна».
    """
    if not last_seen_iso:
        return True
    now = now or datetime.now(UTC)
    try:
        last = datetime.fromisoformat(last_seen_iso)
    except (ValueError, TypeError):
        return True
    if last.tzinfo is None:
        last = last.replace(tzinfo=UTC)
    delta = (now - last).total_seconds() / 60.0
    return delta >= min_gap_minutes


def greeting_context(state, story) -> dict:
    """Собирает контекст для speak_line('morning', **ctx)."""
    from aura.lore.story import StoryLog
    log = story or StoryLog()
    return {
        "day": state.days_on_planet(),
        "sector": state.sector,
        "xp": state.xp,
        "shields": state.shields,
        "reactor": state.reactor,
        "hull": state.hull,
        "modules": len(getattr(state, "modules_active", []) or []),
        "maneuvers": log.count_maneuvers(),
    }
