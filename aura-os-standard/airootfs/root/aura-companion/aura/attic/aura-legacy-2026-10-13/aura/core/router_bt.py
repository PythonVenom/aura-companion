"""Behavior Tree роутер (ADR-094).

Простые узлы: Selector (ИЛИ), Sequence (И), Leaf (действие).
Без LangGraph — 100 строк, ноль зависимостей.
"""
from __future__ import annotations

from collections.abc import Callable


class Node:
    name = "node"

    def handle(self, text: str, ctx: dict) -> str | None:
        raise NotImplementedError


class Selector(Node):
    """ИЛИ: первый узел, вернувший не-None, побеждает."""
    def __init__(self, name: str, children: list):
        self.name = name
        self.children = children

    def handle(self, text, ctx):
        for child in self.children:
            r = child.handle(text, ctx)
            if r is not None:
                return r
        return None


class Sequence(Node):
    """И: все узлы должны сработать, возвращает последний результат."""
    def __init__(self, name: str, children: list):
        self.name = name
        self.children = children

    def handle(self, text, ctx):
        last = None
        for child in self.children:
            r = child.handle(text, ctx)
            if r is None:
                return None
            last = r
        return last


class Leaf(Node):
    """Лист: предикат + действие."""
    def __init__(self, name: str, match: Callable[[str, dict], bool],
                 action: Callable[[str, dict], str]):
        self.name = name
        self._match = match
        self._action = action

    def handle(self, text, ctx):
        if self._match(text, ctx):
            return self._action(text, ctx)
        return None


__all__ = ["Leaf", "Node", "Selector", "Sequence"]
