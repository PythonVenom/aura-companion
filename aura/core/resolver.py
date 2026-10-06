"""Resolution Cascade — 4-ступенчатый поиск цели (ADR-098).

App → Window → Browser Tab → Web.
Первая ступень с результатом побеждает.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class ResolutionStep:
    name: str
    resolve: Callable[[str, dict], str | None]


class ResolutionCascade:
    def __init__(self, steps: list):
        self.steps = steps

    def resolve(self, target: str, ctx: dict | None = None) -> dict:
        ctx = ctx or {}
        for step in self.steps:
            try:
                result = step.resolve(target, ctx)
            except Exception:
                result = None
            if result:
                return {"level": step.name, "value": result}
        return {"level": "none", "value": None}


def make_cascade(
    app_resolver=None,
    window_resolver=None,
    browser_resolver=None,
    web_resolver=None,
) -> ResolutionCascade:
    steps = []
    if app_resolver:
        steps.append(ResolutionStep("app", app_resolver))
    if window_resolver:
        steps.append(ResolutionStep("window", window_resolver))
    if browser_resolver:
        steps.append(ResolutionStep("browser", browser_resolver))
    if web_resolver:
        steps.append(ResolutionStep("web", web_resolver))
    return ResolutionCascade(steps)


__all__ = ["ResolutionCascade", "ResolutionStep", "make_cascade"]
