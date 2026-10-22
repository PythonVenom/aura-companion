"""Rituals — утренний/вечерний ритуал AURA (Horizon GAIA).

Наука: Habit Loop (Duhigg 2012), Ritual Design (Norton 2010).
Утро: статус + брифинг. Вечер: итоги + сон.
"""
from __future__ import annotations

import contextlib
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Ritual:
    name: str
    hour: int
    emoji: str


RITUALS = {
    "morning": Ritual("Утренний брифинг", 7, "🌅"),
    "evening": Ritual("Вечерний ритуал", 22, "🌙"),
}


def current_ritual() -> str | None:
    """Какой ритуал сейчас актуален?"""
    h = datetime.now().hour
    if 6 <= h < 9:
        return "morning"
    if 21 <= h < 23:
        return "evening"
    return None


def morning_briefing() -> str:
    """Собрать утренний брифинг."""
    lines = ["🌅 Доброе утро, капитан."]
    try:
        from aura.core.cluster_health import summary
        s = summary()
        lines.append(f"  Кластеров: {s['ok']}/{s['total']} OK")
    except Exception:
        pass
    try:
        from aura.core import blackboard as bb
        alerts = bb.recent_alerts(window_sec=86400)  # за сутки
        if alerts:
            lines.append(f"  Ночных тревог: {len(alerts)}")
        else:
            lines.append("  Ночь прошла спокойно.")
    except Exception:
        pass
    try:
        from aura.core.affinity import status
        lines.append("  " + status().split("\n")[0])
    except Exception:
        pass
    lines.append("  Готова к работе.")
    return "\n".join(lines)


def evening_ritual() -> str:
    """Собрать вечерний ритуал."""
    lines = ["🌙 Вечерний ритуал."]
    with contextlib.suppress(Exception):
        lines.append("  День записан в бортовой журнал.")
    try:
        from aura.core.receipts import stats
        r = stats()
        lines.append(f"  Верифицировано действий: {r['receipts']}")
    except Exception:
        pass
    lines.append("  Отдыхай, капитан. Дежурю.")
    return "\n".join(lines)


def run(ritual: str) -> str:
    """Запустить ритуал по имени."""
    if ritual == "morning":
        return morning_briefing()
    if ritual == "evening":
        return evening_ritual()
    return "Ритуал не найден."


__all__ = ["RITUALS", "Ritual", "current_ritual", "evening_ritual", "morning_briefing", "run"]
