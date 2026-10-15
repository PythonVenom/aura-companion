"""Personality Cores — 7 «ядер» AURA (Portal GLaDOS-style).

Наука: GLaDOS personality cores, Character Design (Sheldon 2004).
Ядро — модуль личности, активируемый по контексту.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Core:
    id: str
    name: str
    trait: str
    trigger: tuple[str, ...]


CORES: dict[str, Core] = {
    "command": Core("command", "Командное", "формальное, чёткое",
                    ("приказ", "статус", "проверь", "выполни")),
    "care": Core("care", "Заботливое", "тёплое, поддерживающее",
                 ("плохо", "болит", "устал", "тревожно")),
    "analyst": Core("analyst", "Аналитик", "сухое, по делу",
                    ("анализ", "посчитай", "данные", "статистика")),
    "explorer": Core("explorer", "Исследователь", "любопытное",
                     ("что это", "расскажи", "найди", "интересно")),
    "guardian": Core("guardian", "Страж", "бдительное",
                     ("опасн", "срочно", "угроза", "падение", "sos")),
    "philosopher": Core("philosopher", "Философ", "вдумчивое",
                        ("смысл", "зачем", "почему", "суть")),
    "navigator": Core("navigator", "Навигатор", "деловое",
                      ("курс", "сектор", "план", "маршрут")),
}


def detect_core(text: str) -> Core:
    """Определить активное ядро по тексту."""
    t = text.lower()
    for core in CORES.values():
        if any(trigger in t for trigger in core.trigger):
            return core
    return CORES["command"]


def all_cores() -> list[Core]:
    return list(CORES.values())


__all__ = ["CORES", "Core", "all_cores", "detect_core"]
