"""Prospective Memory — обёртка над care (ADR-122, слой 6).

Наука: Einstein, G. O. & McDaniel, M. A. (1990). Normal aging and prospective memory.
       Journal of Experimental Psychology: Learning, Memory, and Cognition.

Aura: напоминания, задачи, ритуалы (что нужно сделать в будущем).
"""
from __future__ import annotations


class ProspectiveMemory:
    def __init__(self) -> None:
        self._agent = None
        self._ready = False
        self._init()

    def _init(self) -> None:
        try:
            from aura.agents.care import CareAgent
            self._agent = CareAgent()
            self._ready = True
        except Exception as e:
            print(f"⚠️ Prospective init: {e}")

    def check_ready(self) -> bool:
        return self._ready

    def tasks(self) -> list[dict]:
        if not self._ready:
            return []
        try:
            return [{"name": t.name, "times": t.times, "message": t.message}
                    for t in self._agent.tasks]
        except Exception:
            return []

    def add_task(self, name: str, times: list[str], message: str = "") -> bool:
        if not self._ready:
            return False
        try:
            self._agent.add_task(name, times, message)
            self._agent._save()
            return True
        except Exception:
            return False

    def stats(self) -> dict:
        if not self._ready:
            return {"ready": False}
        return {"ready": True, "count": len(self._agent.tasks)}


_SINGLETON: ProspectiveMemory | None = None


def get_prospective() -> ProspectiveMemory:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = ProspectiveMemory()
    return _SINGLETON
