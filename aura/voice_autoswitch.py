"""Voice Profile autoswitch по контексту (ADR-044).

Утро -> sport, работа -> massage, вечер -> dev, ночь -> default.
"""
from __future__ import annotations

from datetime import datetime


# Контексты дня: (начало_час, конец_час, profile)
SCHEDULE = [
    (6, 9, "sport"),        # 06-09
    (9, 18, "massage"),     # 09-18
    (18, 21, "construction"),  # 18-21
    (21, 23, "dev"),        # 21-23
    (23, 6, "default"),     # ночь
]


def get_current_profile(now: datetime | None = None) -> str:
    """Какой профиль сейчас по расписанию."""
    now = now or datetime.now()
    h = now.hour
    for start, end, profile in SCHEDULE:
        if start <= end:
            if start <= h < end:
                return profile
        else:  # ночь (23-6)
            if h >= start or h < end:
                return profile
    return "default"


def should_switch(current_setting: str, now: datetime | None = None) -> str | None:
    """Вернуть новый профиль если надо переключить, иначе None."""
    target = get_current_profile(now)
    if target != current_setting:
        return target
    return None


__all__ = ["get_current_profile", "should_switch", "SCHEDULE"]
