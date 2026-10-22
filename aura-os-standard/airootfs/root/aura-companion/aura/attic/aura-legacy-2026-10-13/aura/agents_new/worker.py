"""Worker Agent v0.3 — реальное исполнение через executors.
Наука: Orchestrator-Worker + Capability-based execution.
"""
import asyncio
import json
import logging
from pathlib import Path

from aura.agents_new.executors import get_executor
from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log

log = logging.getLogger("aura.worker")
QUEUE_PATH = Path.home() / "aura_project/tasks/queue.jsonl"


class WorkerAgent:
    name = "worker"
    version = "0.3.0"

    def __init__(self, dry_run: bool = True):
        self.ctx: AgentContext | None = None
        self._running = False
        self.dry_run = dry_run

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        log.info("worker started (dry_run=%s)", self.dry_run)
        event_log.append("agent.started",
                         {"name": self.name, "dry_run": self.dry_run, "v": self.version},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "dry_run": self.dry_run, "version": self.version}

    async def stop(self) -> None:
        self._running = False
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)

    def _read_tasks(self) -> list:
        if not QUEUE_PATH.exists():
            return []
        return [json.loads(l) for l in QUEUE_PATH.read_text().splitlines() if l.strip()]

    def _write_tasks(self, tasks: list):
        QUEUE_PATH.write_text(
            "\n".join(json.dumps(t, ensure_ascii=False) for t in tasks) + "\n")

    async def tick(self):
        tasks = self._read_tasks()
        changed = False
        for t in tasks:
            if t.get("status") != "doing":
                continue
            task_id = t["id"]
            executor = get_executor(task_id)
            if executor is None:
                log.info("worker %s: нет executor — skip", task_id)
                continue
            try:
                ok, msg = await executor(t)
                if self.dry_run:
                    log.info("worker %s: DRY-RUN — %s", task_id, msg)
                    event_log.append("task.dry_run",
                                     {"id": task_id, "ok": ok, "msg": msg},
                                     src=self.name)
                else:
                    t["status"] = "done" if ok else "failed"
                    log.info("worker %s: %s — %s", task_id, t["status"], msg)
                    event_log.append(
                        "task.completed" if ok else "task.failed",
                        {"id": task_id, "msg": msg},
                        src=self.name)
                    changed = True
            except Exception as e:
                log.exception("worker %s failed: %s", task_id, e)
                if not self.dry_run:
                    t["status"] = "failed"
                    changed = True
                event_log.append("task.error",
                                 {"id": task_id, "error": str(e)},
                                 src=self.name)
        if changed:
            self._write_tasks(tasks)

    async def run_loop(self, interval: float = 2.0):
        while self._running:
            try:
                await self.tick()
            except Exception as e:
                log.exception("worker tick failed: %s", e)
            await asyncio.sleep(interval)
