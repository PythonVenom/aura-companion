"""Meds Agent v1.1 — kernel-адаптер над старым AgentMeds.
Не переписываем — оборачиваем. Тот же SQLite, та же логика.
Наука: Adapter Pattern (Gamma et al.), Strangler Fig (Fowler).
"""
import logging

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log
from aura.kernel.payload import get_payload

log = logging.getLogger("aura.agents.meds")


class MedsAgent:
    name = "meds"
    version = "1.1.0"

    def __init__(self):
        self.ctx: AgentContext | None = None
        self._running = False
        self._legacy = None

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        # Импортируем старый агент — оборачиваем, не переписываем
        from aura.agents.meds import AgentMeds
        self._legacy = AgentMeds()
        log.info("meds adapter started (legacy=%s)", type(self._legacy).__name__)
        event_log.append("agent.started",
                         {"name": self.name, "v": self.version,
                          "legacy": "AgentMeds"},
                         src=self.name)
        # Подписки на шину
        ctx.bus.subscribe("meds.add", self._on_add)
        ctx.bus.subscribe("meds.list", self._on_list)
        ctx.bus.subscribe("meds.taken", self._on_taken)
        ctx.bus.subscribe("meds.tick", self._on_tick)

    async def handle(self, event: Event) -> None:
        pass

    async def _call_legacy(self, text: str):
        """Вызов старого handle через AgentRequest/AgentResponse."""
        from aura.core.protocol import AgentRequest
        req = AgentRequest(text=text, user_id="batya", source="kernel")
        if not self._legacy.can_handle(req):
            return None
        return await self._legacy.handle(req)

    async def _on_add(self, event) -> None:
        p = get_payload(event)
        name = p.get("name", "")
        time_str = p.get("time", "")
        dose = p.get("dose", "")
        text = f"добавь лекарство {name}"
        if dose:
            text += f" {dose}"
        if time_str:
            text += f" в {time_str}"
        try:
            resp = await self._call_legacy(text)
            msg = resp.text if resp else "не распознано"
            event_log.append("meds.added",
                             {"name": name, "time": time_str, "result": msg},
                             src=self.name)
            if self.ctx:
                await self.ctx.bus.publish("meds.added",
                                           {"name": name, "time": time_str,
                                            "result": msg})
        except Exception as e:
            log.exception("meds.add failed: %s", e)
            event_log.append("meds.error", {"error": str(e)}, src=self.name)

    async def _on_list(self, event) -> None:
        try:
            resp = await self._call_legacy("покажи список лекарств")
            text = resp.text if resp else "пусто"
            event_log.append("meds.listed", {"result": text[:200]}, src=self.name)
            if self.ctx:
                await self.ctx.bus.publish("meds.list_result", {"text": text})
        except Exception as e:
            log.exception("meds.list failed: %s", e)

    async def _on_taken(self, event) -> None:
        try:
            resp = await self._call_legacy("принял лекарство")
            text = resp.text if resp else "ок"
            event_log.append("meds.taken", {"result": text[:200]}, src=self.name)
        except Exception as e:
            log.exception("meds.taken failed: %s", e)

    async def _on_tick(self, event) -> None:
        """Проверить, не пора ли напомнить. Legacy сам решает."""
        try:
            resp = await self._call_legacy("статус лекарств")
            if resp and "пора" in resp.text.lower():
                event_log.append("meds.reminder",
                                 {"text": resp.text}, src=self.name)
                if self.ctx:
                    await self.ctx.bus.publish("meds.reminder",
                                               {"text": resp.text})
        except Exception as e:
            log.debug("meds tick: %s", e)

    async def health(self) -> dict:
        return {
            "status": "ok" if self._running else "stopped",
            "version": self.version,
            "legacy": self._legacy is not None,
        }

    async def stop(self) -> None:
        self._running = False
        if self.ctx:
            for topic in ("meds.add", "meds.list", "meds.taken", "meds.tick"):
                for h in list(self.ctx.bus._subs.get(topic, [])):
                    self.ctx.bus.unsubscribe(topic, h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
