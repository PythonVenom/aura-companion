"""Weather Agent v1.1 — kernel-адаптер над AgentWeather.
Погода через wttr.in. On-demand.
Наука: Adapter Pattern + Elder-care (Czaja 2018).
"""
import logging

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log
from aura.kernel.payload import get_payload

log = logging.getLogger("aura.agents.weather")


class WeatherAgent:
    name = "weather"
    version = "1.1.0"

    def __init__(self):
        self.ctx: AgentContext | None = None
        self._running = False
        self._legacy = None

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        from aura.agents.weather import WeatherAgent as AgentWeather  # type: ignore[attr-defined]
        self._legacy = AgentWeather()
        ctx.bus.subscribe("weather.ask", self._on_ask)
        log.info("weather adapter started")
        event_log.append("agent.started",
                         {"name": self.name, "v": self.version,
                          "legacy": "AgentWeather",
                          "city": "unknown"},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _on_ask(self, event) -> None:
        p = get_payload(event)
        text = p.get("text", "погода")
        try:
            from aura.core.protocol import AgentRequest
            req = AgentRequest(text=text, user_id="batya", source="kernel")
            resp = await self._legacy.handle(req)
            out = resp.text if resp else "Не могу узнать погоду"
            event_log.append("weather.answer",
                             {"query": text[:60], "result": out[:200]},
                             src=self.name)
            if self.ctx:
                await self.ctx.bus.publish("weather.answer", {"text": out})
        except Exception as e:
            log.exception("weather failed: %s", e)
            if self.ctx:
                await self.ctx.bus.publish("weather.answer",
                                           {"text": f"Погода недоступна: {e}"})

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "version": self.version,
                "legacy": self._legacy is not None}

    async def stop(self) -> None:
        self._running = False
        if self.ctx:
            for h in list(self.ctx.bus._subs.get("weather.ask", [])):
                self.ctx.bus.unsubscribe("weather.ask", h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
