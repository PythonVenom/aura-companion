"""Capability Dispatcher — реальный executor для ReAct (ADR-104).

Связывает capability name → handler (агент + метод).
"""
from __future__ import annotations
from typing import Callable, Optional


# Реестр handlers: capability → callable(args) → (ok, result)
_HANDLERS: dict = {}


def register(capability: str, handler: Callable) -> None:
    _HANDLERS[capability] = handler


def get_handler(capability: str) -> Optional[Callable]:
    return _HANDLERS.get(capability)


def dispatch(capability: str, args: dict) -> tuple:
    """(ok, result_or_error)"""
    h = _HANDLERS.get(capability)
    if h is None:
        return False, f"no handler for {capability}"
    try:
        result = h(args)
        return True, str(result)[:500]
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def list_registered() -> list:
    return sorted(_HANDLERS.keys())


def _register_defaults():
    """MVP: несколько прямых handlers для smoke."""
    # world.state — просто текст
    def world_state(args):
        from aura.core.world_model import get_world
        w = get_world()
        w.refresh()
        return w.summary()

    # context.recent — что делал
    def context_recent(args):
        from aura.core.context import get_context
        c = get_context()
        mins = args.get("minutes", 10)
        return c.summary(minutes=mins)

    register("world.state", world_state)
    register("context.recent", context_recent)


# Автозагрузка defaults при первом импорте
if not _HANDLERS:
    _register_defaults()


__all__ = ["register", "get_handler", "dispatch", "list_registered"]
