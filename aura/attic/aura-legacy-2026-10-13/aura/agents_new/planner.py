"""Planner Agent — читает queue.jsonl, публикует задачи в шину.
Наука: Orchestrator-Worker Pattern (Kubernetes, Temporal).
"""
import asyncio
import json
import logging
from pathlib import Path

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log

log = logging.getLogger("aura.planner")

QUEUE_PATH = Path.home() / "aura_project/tasks/queue.jsonl"


class PlannerAgent:
    name = "planner"
    version = "0.1.0"

    def __init__(self):
        self.ctx: AgentContext | None = None
        self._running = False

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        log.info("planner started")
        event_log.append("agent.started", {"name": self.name}, src=self.name)

    async def handle(self, event: Event) -> None:
        # Planner не реагирует на события, он сам генерирует
        pass

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "queue": str(QUEUE_PATH)}

    async def stop(self) -> None:
        self._running = False
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)

    def _read_tasks(self) -> list:
        if not QUEUE_PATH.exists():
            return []
        tasks = []
        with open(QUEUE_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        tasks.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return tasks

    def _write_tasks(self, tasks: list):
        with open(QUEUE_PATH, "w", encoding="utf-8") as f:
            for t in tasks:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")

    async def tick(self):
        """Один цикл: взять todo → published → пометить doing."""
        tasks = self._read_tasks()
        changed = False
        for t in tasks:
            if t.get("status") == "todo":
                t["status"] = "doing"
                changed = True
                log.info("assigned: %s — %s", t["id"], t["title"])
                event_log.append("task.assigned",
                                 {"id": t["id"], "title": t["title"],
                                  "agent": t.get("agent", "?")},
                                 src=self.name)
                await self.ctx.bus.publish("task.assigned", t)
        if changed:
            self._write_tasks(tasks)

    async def run_loop(self, interval: float = 2.0):
        while self._running:
            try:
                await self.tick()
            except Exception as e:
                log.exception("planner tick failed: %s", e)
            await asyncio.sleep(interval)
