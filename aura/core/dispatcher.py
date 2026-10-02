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

    # care.list
    def care_list(args):
        from aura.agents.care import CareAgent
        a = CareAgent()
        lines = [f"{t.name}: {', '.join(t.times)} — {t.message}" for t in a.tasks]
        return "\n".join(lines) or "нет напоминаний"

    # care.add
    def care_add(args):
        from aura.agents.care import CareAgent
        a = CareAgent()
        a.add_task(args.get("name", "task"), args.get("times", []), args.get("msg", ""))
        a._save()
        return f"added {args.get('name')}"

    # journal.stats
    def journal_stats(args):
        from aura.agents.journal_mood import VoiceJournal
        j = VoiceJournal()
        s = j.stats_last_days(args.get("days", 7))
        return f"За {args.get('days', 7)} дней: {s['count']} записей, среднее {s['avg']}"

    # journal.add
    def journal_add(args):
        from aura.agents.journal_mood import VoiceJournal
        j = VoiceJournal()
        j.add(args.get("text", ""), args.get("mood"))
        return f"записано: mood={args.get('mood')}"

    # recon.run
    def recon_run(args):
        import subprocess, sys
        from pathlib import Path as P
        r = subprocess.run(
            [sys.executable, str(P(__file__).parent.parent.parent / "scripts/aura_recon.py"),
             "base", "--out", "/tmp/aura_recon_latest.md", "--quiet"],
            capture_output=True, text=True, timeout=30,
        )
        return "recon OK" if r.returncode == 0 else f"recon err: {r.stderr[:100]}"

    # focus.enable
    def focus_enable(args):
        from aura.core import focus
        focus.enable(seconds=args.get("minutes", 60) * 60)
        return f"focus {args.get('minutes', 60)} min"

    # focus.disable
    def focus_disable(args):
        from aura.core import focus
        focus.disable()
        return "focus off"

    # handsfree.on / off
    def handsfree_on(args):
        from aura.core import hands_free
        hands_free.enable(seconds=args.get("seconds", 300))
        return "handsfree on"

    def handsfree_off(args):
        from aura.core import hands_free
        hands_free.disable()
        return "handsfree off"

    register("world.state", world_state)
    register("context.recent", context_recent)
    register("care.list", care_list)
    register("care.add", care_add)
    register("journal.stats", journal_stats)
    register("journal.add", journal_add)
    register("recon.run", recon_run)
    register("focus.enable", focus_enable)
    register("focus.disable", focus_disable)
    register("handsfree.on", handsfree_on)
    register("handsfree.off", handsfree_off)


# Автозагрузка defaults при первом импорте
if not _HANDLERS:
    _register_defaults()


__all__ = ["register", "get_handler", "dispatch", "list_registered"]
