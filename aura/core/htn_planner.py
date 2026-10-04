"""HTN Planner — декомпозиция цели на подзадачи (ADR-102).

Method: цель → список шагов
Operator: конкретное действие (capability + args)
Planner.plan(goal) → list[Operator]

MVP: реестр методов без LLM. Позже — LLM-декомпозиция.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Operator:
    capability: str           # "browser.open"
    args: dict = field(default_factory=dict)
    description: str = ""


@dataclass
class Method:
    name: str                 # "write_site"
    triggers: list            # ["напиши сайт", "создай сайт"]
    steps: list               # list[Operator] или callable
    description: str = ""


class Planner:
    def __init__(self):
        self.methods: list = []

    def add_method(self, method: Method) -> None:
        self.methods.append(method)

    def find_method(self, goal: str) -> Optional[Method]:
        g = goal.lower()
        for m in self.methods:
            if any(t in g for t in m.triggers):
                return m
        return None

    def plan(self, goal: str) -> list:
        m = self.find_method(goal)
        if m is None:
            return []
        # Если steps — callable, вызываем с goal
        if callable(m.steps):
            return m.steps(goal)
        return list(m.steps)

    def all_methods(self) -> list:
        return [m.name for m in self.methods]


def build_default_methods() -> Planner:
    p = Planner()
    # 1. Открой X → cascade
    p.add_method(Method(
        name="open_target",
        triggers=["открой", "запусти"],
        steps=[
            Operator("browser.open", {"target": "X"}, "открыть в браузере"),
        ],
        description="открыть цель через Cascade",
    ))
    # 2. Проверка системы
    p.add_method(Method(
        name="system_check",
        triggers=["что в системе", "состояние", "диагностика"],
        steps=[
            Operator("world.state", {}, "собрать состояние"),
            Operator("recon.run", {}, "запустить recon"),
        ],
        description="обзор системы",
    ))
    # 3. Утренний брифинг (заготовка)
    p.add_method(Method(
        name="morning_briefing",
        triggers=["брифинг", "утренний отчёт", "что нового"],
        steps=[
            Operator("context.recent", {"minutes": 720}, "что было"),
            Operator("care.list", {}, "напоминания"),
            Operator("journal.stats", {"days": 1}, "настроение"),
        ],
        description="утренний отчёт",
    ))
    # 4. Фокус-сессия
    p.add_method(Method(
        name="focus_session",
        triggers=["фокус", "не отвлекать", "работать"],
        steps=[
            Operator("focus.enable", {"minutes": 60}, "включить фокус"),
            Operator("music.play", {"query": "focus"}, "включить музыку"),
        ],
        description="фокус-сессия",
    ))
    return p


_planner = None


def get_planner() -> Planner:
    global _planner
    if _planner is None:
        _planner = build_default_methods()
    return _planner


__all__ = ["Operator", "Method", "Planner", "build_default_methods", "get_planner"]
