"""Care Agent v1.1 — kernel-адаптер над CareAgent.
Напоминания: вода, еда, сон. Timer + шина.
Наука: Adapter Pattern + Habit Loop (Duhigg 2012).
"""
import asyncio
import logging

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log

log = logging.getLogger("aura.agents.care")


class CareAgent:
    name = "care"
    version = "1.1.0"

    def __init__(self):
        self.ctx: AgentContext | None = None
        self._running = False
        self._legacy = None
        self._timer_task = None

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        from aura.agents.care import CareAgent as LegacyCare
        self._legacy = LegacyCare()
        ctx.bus.subscribe("care.tick", self._on_tick)
        ctx.bus.subscribe("care.list", self._on_list)
        ctx.bus.subscribe("care.morning", self._on_morning)
        self._timer_task = asyncio.create_task(self._timer_loop(60))
        log.info("care adapter started (timer 60s)")
        event_log.append("agent.started",
                         {"name": self.name, "v": self.version,
                          "legacy": "CareAgent", "timer": 60},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _timer_loop(self, interval: float):
        """Каждую минуту — проверка due tasks."""
        while self._running:
            try:
                await asyncio.sleep(interval)
                await self.ctx.bus.publish("care.tick", {})  # type: ignore[union-attr]
            except asyncio.CancelledError:
                return
            except Exception as e:
                log.exception("care timer error: %s", e)

    async def _on_morning(self, event) -> None:
        """AURA_CARE_MORNING_V1: утреннее приветствие."""
        from datetime import datetime
        hour = datetime.now().hour
        if 6 <= hour < 11:
            text = "Доброе утро, батя. Как спалось?"
        elif 11 <= hour < 17:
            text = "Добрый день, батя. Как дела?"
        elif 17 <= hour < 23:
            text = "Добрый вечер, батя. Как прошёл день?"
        else:
            text = "Поздно, батя. Пора спать."
        event_log.append("care.morning", {"text": text}, src=self.name)
        if self.ctx:
            await self.ctx.bus.publish("care.greeting", {"text": text})

    async def _on_tick(self, event) -> None:
        try:
            from datetime import datetime
            # AURA_CARE_MORNING_TRIGGER_V1: в 8:00 утреннее приветствие
            now = datetime.now()
            if now.hour == 8 and now.minute < 2:
                await self._on_morning(event)
            due = self._legacy.get_due_tasks(datetime.now())
            for task in due:
                text = task.message or f"Пора: {task.name}"
                log.info("care reminder: %s", text)
                event_log.append("care.reminder",
                                 {"task": task.name, "text": text},
                                 src=self.name)
                if self.ctx:
                    await self.ctx.bus.publish("care.reminder",
                                               {"text": text})
        except Exception as e:
            log.exception("care tick failed: %s", e)

    async def _on_list(self, event) -> None:
        try:
            names = [t.name for t in self._legacy.tasks if t.enabled]
            text = f"Забота: {', '.join(names)}" if names else "Забот нет"
            event_log.append("care.list", {"tasks": names}, src=self.name)
            if self.ctx:
                await self.ctx.bus.publish("care.answer", {"text": text})
        except Exception as e:
            log.exception("care list failed: %s", e)

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "version": self.version,
                "legacy": self._legacy is not None}

    async def stop(self) -> None:
        self._running = False
        if self._timer_task:
            self._timer_task.cancel()
        if self.ctx:
            for t in ("care.tick", "care.list", "care.morning"):
                for h in list(self.ctx.bus._subs.get(t, [])):
                    self.ctx.bus.unsubscribe(t, h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
