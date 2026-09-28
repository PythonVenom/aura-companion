"""HealthAgent — напоминания о здоровье."""
from __future__ import annotations
import json
import time
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent

HEALTH_PATH = Path("/tmp/aura_health.json")


def _load():
    if not HEALTH_PATH.exists():
        return []
    try:
        return json.loads(HEALTH_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(items):
    try:
        HEALTH_PATH.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def add_reminder(text, every_minutes=60):
    item = {"id": int(time.time() * 1000), "text": text,
            "every_sec": every_minutes * 60,
            "next_at": time.time() + every_minutes * 60}
    items = _load(); items.append(item); _save(items); return item


def list_reminders():
    return _load()


def check_due():
    now = time.time()
    items = _load()
    due = []; changed = False
    for it in items:
        if it.get("next_at", 0) <= now:
            due.append(it)
            it["next_at"] = now + it.get("every_sec", 3600)
            changed = True
    if changed:
        _save(items)
    return due


class AgentHealth(BaseAgent):
    name = "health"
    MODULE_ALWAYS = True
    KEYWORDS = ("лекарств", "таблетк", "попить воды", "перерыв",
                "напоминай про", "здоровье")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        if "напомни" in text or "напоминай" in text:
            every = 60
            if "30 минут" in text:
                every = 30
            elif "15 минут" in text:
                every = 15
            add_reminder(text, every)
            return AgentResponse.ok(f"💊 Напоминание каждые {every} мин", self.name)

        if "какие" in text or "покажи" in text:
            items = list_reminders()
            if not items:
                return AgentResponse.ok("💊 Напоминаний нет", self.name)
            parts = [it["text"][:40] for it in items[:5]]
            return AgentResponse.ok("💊 " + ", ".join(parts), self.name)

        return AgentResponse.not_handled(self.name)
