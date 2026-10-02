"""ReAct Loop — Reason + Act + Observe + Reflect (ADR-103).

Итеративный цикл: план → действие → наблюдение → оценка → повтор.
Используется для многошаговых задач («напиши сайт», «почини X»).

MVP: 3 итерации макс, рефлексия через простые эвристики.
Позже — LLM-рефлексия.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Step:
    iteration: int
    operator: str
    args: dict
    result: str = ""
    ok: bool = False
    error: str = ""


@dataclass
class Episode:
    goal: str
    steps: list = field(default_factory=list)
    done: bool = False
    reason: str = ""


class ReActLoop:
    MAX_ITERATIONS = 3

    def __init__(self, executor: Callable, reflector: Callable = None):
        """executor(operator, args) → (ok, result_or_error)
        reflector(goal, steps) → (done: bool, reason: str)
        """
        self.executor = executor
        self.reflector = reflector or self._default_reflector

    def _default_reflector(self, goal: str, steps: list) -> tuple:
        """Simple: done если все шаги ok, иначе нет."""
        if not steps:
            return False, "no steps executed"
        if all(s.ok for s in steps):
            return True, "all steps succeeded"
        return False, f"failed: {[s.error for s in steps if not s.ok]}"

    def run(self, goal: str, operators: list) -> Episode:
        ep = Episode(goal=goal)
        for i, op in enumerate(operators[:self.MAX_ITERATIONS], 1):
            step = Step(iteration=i, operator=op.capability, args=op.args)
            try:
                ok, result = self.executor(op.capability, op.args)
                step.ok = bool(ok)
                step.result = str(result)[:200]
            except Exception as e:
                step.ok = False
                step.error = str(e)
            ep.steps.append(step)

        ep.done, ep.reason = self.reflector(goal, ep.steps)
        return ep


def format_episode(ep: Episode) -> str:
    lines = [f"Цель: {ep.goal}", f"Статус: {'DONE' if ep.done else 'FAILED'}"]
    for s in ep.steps:
        mark = "OK" if s.ok else "ERR"
        lines.append(f"  {s.iteration}. [{mark}] {s.operator} → {s.result or s.error}")
    lines.append(f"Итог: {ep.reason}")
    return "\n".join(lines)


__all__ = ["Step", "Episode", "ReActLoop", "format_episode"]
