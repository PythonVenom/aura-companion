"""Proactive Alert Agent v1.1 — kernel-адаптер над AgentProactiveAlert.
Детектор тишины + эскалация. Разрываем прямые вызовы — всё через шину.
Наука: Inactivity Detection (Kasteren 2011) + Escalation Protocol.
"""
import asyncio
import logging

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log
from aura.kernel.payload import get_payload

log = logging.getLogger("aura.agents.proactive_alert")


class ProactiveAlertAgent:
    name = "proactive_alert"
    version = "1.1.0"

    def __init__(self):
        self.ctx: AgentContext | None = None
        self._running = False
        self._legacy = None
        self._timer_task = None

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        from aura.agents.proactive_alert import AgentProactiveAlert
        self._legacy = AgentProactiveAlert()
        ctx.bus.subscribe("proactive.tick", self._on_tick)  # type: ignore[union-attr]
        ctx.bus.subscribe("proactive.touch", self._on_touch)
        ctx.bus.subscribe("proactive.status", self._on_status)
        ctx.bus.subscribe("proactive.set_threshold", self._on_set_threshold)
        # Автозапуск таймера: каждые 5 минут проверка
        self._timer_task = asyncio.create_task(self._timer_loop(300))
        log.info("proactive_alert adapter started (timer 5m)")
        event_log.append("agent.started",
                         {"name": self.name, "v": self.version,
                          "legacy": "AgentProactiveAlert", "timer": 300},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _timer_loop(self, interval: float):
        """Каждые N секунд публикуем proactive.tick."""
        while self._running:
            try:
                await asyncio.sleep(interval)
                await self.ctx.bus.publish("proactive.tick", {})  # type: ignore[union-attr]
            except asyncio.CancelledError:
                return
            except Exception as e:
                log.exception("timer error: %s", e)

    def _safety_enabled(self) -> bool:
        """AURA_SAFE_MODE_V1: proactive off если не включён в конфиге."""
        import json
        from pathlib import Path
        cfg = Path.home() / ".config/aura/safety.json"
        if not cfg.exists():
            return False
        try:
            data = json.loads(cfg.read_text())
            return data.get("proactive_alert", {}).get("enabled", False)
        except Exception:
            return False

    async def _on_tick(self, event) -> None:
        try:
            if not self._safety_enabled():
                return
            if self._legacy.check():
                since = self._legacy._since_last()
                threshold = self._legacy._threshold()
                text = (f"Батя молчит {since:.1f}ч (порог {threshold:.1f}ч). "
                        f"Проверяю, звоню.")
                log.warning("proactive alert: %s", text)
                event_log.append("proactive.alert",
                                 {"since_h": since, "threshold_h": threshold},
                                 src=self.name)
                if self.ctx:
                    await self.ctx.bus.publish("proactive.alert",
                                               {"text": text,
                                                "since_h": since})
        except Exception as e:
            log.exception("proactive tick failed: %s", e)

    async def _on_touch(self, event) -> None:
        try:
            self._legacy.touch()
            self._legacy.clear_alert()
            event_log.append("proactive.touched", {}, src=self.name)
        except Exception as e:
            log.warning("touch failed: %s", e)

    async def _on_status(self, event) -> None:
        try:
            since = self._legacy._since_last()
            threshold = self._legacy._threshold()
            text = f"Тишина {since:.1f}ч / порог {threshold:.1f}ч"
            event_log.append("proactive.status",
                             {"since_h": since, "threshold_h": threshold},
                             src=self.name)
            if self.ctx:
                await self.ctx.bus.publish("proactive.status_result",
                                           {"text": text})
        except Exception as e:
            log.warning("status failed: %s", e)

    async def _on_set_threshold(self, event) -> None:
        p = get_payload(event)
        hours = p.get("hours")
        if hours is None:
            return
        try:
            self._legacy._set("threshold_hours", float(hours))
            event_log.append("proactive.threshold_set",
                             {"hours": float(hours)}, src=self.name)
        except Exception as e:
            log.warning("set_threshold failed: %s", e)

    async def health(self) -> dict:
        return {
            "status": "ok" if self._running else "stopped",
            "version": self.version,
            "legacy": self._legacy is not None,
            "timer": self._timer_task is not None,
        }

    async def stop(self) -> None:
        self._running = False
        if self._timer_task:
            self._timer_task.cancel()
        if self.ctx:
            for topic in ("proactive.tick", "proactive.touch",
                          "proactive.status", "proactive.set_threshold"):
                for h in list(self.ctx.bus._subs.get(topic, [])):
                    self.ctx.bus.unsubscribe(topic, h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
