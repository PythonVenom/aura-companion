"""Calendar Agent v1.1 — kernel-адаптер над AgentCalendar.
Наука: Adapter Pattern (Gamma et al.), Strangler Fig (Fowler).
"""
import logging

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log
from aura.kernel.payload import get_payload

log = logging.getLogger("aura.agents.calendar")


class CalendarAgent:
    name = "calendar"
    version = "1.1.0"

    def __init__(self):
        self.ctx: AgentContext | None = None
        self._running = False
        self._legacy = None

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        from aura.agents.calendar import AgentCalendar
        self._legacy = AgentCalendar()
        ctx.bus.subscribe("calendar.add", self._on_add)
        ctx.bus.subscribe("calendar.today", self._on_today)
        ctx.bus.subscribe("calendar.tomorrow", self._on_tomorrow)
        log.info("calendar adapter started")
        event_log.append("agent.started",
                         {"name": self.name, "v": self.version,
                          "legacy": "AgentCalendar"},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _call_legacy(self, text: str):
        from aura.core.protocol import AgentRequest
        req = AgentRequest(text=text, user_id="batya", source="kernel")
        if not self._legacy.can_handle(req):
            return None
        return await self._legacy.handle(req)

    async def _on_add(self, event) -> None:
        p = get_payload(event)
        text = p.get("text", "")
        if not text:
            return
        try:
            resp = await self._call_legacy(f"запиши {text}")
            out = resp.text if resp else "не распознано"
            event_log.append("calendar.added", {"text": text[:80], "result": out[:200]}, src=self.name)
            if self.ctx:
                await self.ctx.bus.publish("calendar.added", {"text": out})
        except Exception as e:
            log.exception("calendar.add failed: %s", e)

    async def _on_today(self, event) -> None:
        try:
            resp = await self._call_legacy("что у меня на сегодня")
            out = resp.text if resp else "пусто"
            event_log.append("calendar.today", {"result": out[:200]}, src=self.name)
            if self.ctx:
                await self.ctx.bus.publish("calendar.answer", {"text": out})
        except Exception as e:
            log.exception("calendar.today failed: %s", e)

    async def _on_tomorrow(self, event) -> None:
        try:
            resp = await self._call_legacy("что на завтра")
            out = resp.text if resp else "пусто"
            event_log.append("calendar.tomorrow", {"result": out[:200]}, src=self.name)
            if self.ctx:
                await self.ctx.bus.publish("calendar.answer", {"text": out})
        except Exception as e:
            log.exception("calendar.tomorrow failed: %s", e)

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "version": self.version,
                "legacy": self._legacy is not None}

    async def stop(self) -> None:
        self._running = False
        if self.ctx:
            for t in ("calendar.add", "calendar.today", "calendar.tomorrow"):
                for h in list(self.ctx.bus._subs.get(t, [])):
                    self.ctx.bus.unsubscribe(t, h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
