"""Voice Profile autoswitch по контексту (ADR-044)."""
from __future__ import annotations

from datetime import datetime

SCHEDULE = [
    (6, 9, "sport"),
    (9, 18, "massage"),
    (18, 21, "construction"),
    (21, 23, "dev"),
    (23, 6, "default"),
]


def get_current_profile(now: datetime | None = None) -> str:
    now = now or datetime.now()
    h = now.hour
    for start, end, profile in SCHEDULE:
        if start <= end:
            if start <= h < end:
                return profile
        else:
            if h >= start or h < end:
                return profile
    return "default"


def should_switch(current_setting: str, now: datetime | None = None) -> str | None:
    target = get_current_profile(now)
    return target if target != current_setting else None


def apply_if_changed() -> str | None:
    """Runtime hook: читает settings, переключает если нужно."""
    try:
        from aura import settings
        cur = settings.get("voice_profile", "default")
        new = should_switch(cur)
        if new:
            settings.set_value("voice_profile", new)
            return new
    except Exception:
        pass
    return None


__all__ = ["get_current_profile", "should_switch", "apply_if_changed", "SCHEDULE"]
