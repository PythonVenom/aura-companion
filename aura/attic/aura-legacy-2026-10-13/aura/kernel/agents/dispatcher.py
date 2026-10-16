"""Dispatcher Agent — текст → топик. Keyword-based routing.
Наука: Mediator Pattern, Content-Based Router (Hohpe & Woolf).
"""
import logging

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log
from aura.kernel.payload import get_payload

log = logging.getLogger("aura.agents.dispatcher")


class DispatcherAgent:
    name = "dispatcher"
    version = "1.0.0"

    # Правила: ключевые слова → топик
    RULES = (
        (("время", "час", "сколько времени", "который час"), "time.ask"),
        (("таблетк", "лекарств", "принять", "выпить"), "meds.list"),
        (("упал", "упала", "помогите", "плохо мне", "не могу встать"), "fall.trigger"),
        (("тревога", "молчит", "проверь батю", "тишина"), "proactive.status"),
        # T-023: calendar
        (("что на сегодня", "что на завтра", "что в календаре",
          "мои встречи", "расписание"), "calendar.today"),
        (("запиши", "напомни", "встреча", "клиент"), "calendar.add"),
        # T-022: weather (надеть/одеться — тоже сюда)
        (("погода", "прогноз", "дождь", "снег", "холодно",
          "тепло", "жарко", "ветер", "градус",
          "надеть", "одеть", "одеться"), "weather.ask"),
        # T-021: care list
        (("забота", "пить воду", "поесть", "поспать"), "care.list"),
        # T-027: care утреннее приветствие
        (("доброе утро", "добрый день", "добрый вечер",
          "как спалось"), "care.morning"),
        # T-028: mentor
        (("что мне делать", "что учить", "следующий шаг"), "mentor.next"),
        (("мой прогресс", "мои навыки", "статистика"), "mentor.stats"),

        # T-029: smarthome
        (("включи свет", "выключи свет", "свет в", "яркость"), "home.light.set"),
        (("включи лампу", "выключи лампу"), "home.light.on"),
        # T-030: messengers
        (("напиши в вк", "напиши вк"), "vk.send"),
        (("напиши в макс", "напиши max"), "max.send"),
        (("напиши в вотсап", "напиши whatsapp"), "wa.send"),
        (("отправь почту", "напиши письмо"), "email.send"),
        (("напиши в телеграм", "напиши в тг"), "telegram.send"),
        # T-031: stop/resume
        (("стоп", "замолчи", "тихо", "хватит"), "stop.speaking"),
        (("продолжи", "дальше", "продолжай", "верни"), "resume.audio"),
    )

    def __init__(self):
        self.ctx: AgentContext | None = None
        self._running = False

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        ctx.bus.subscribe("voice.heard", self._on_voice)
        log.info("dispatcher started (%d rules)", len(self.RULES))
        event_log.append("agent.started",
                         {"name": self.name, "v": self.version,
                          "rules": len(self.RULES)},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _on_voice(self, event) -> None:
        p = get_payload(event)
        text = (p.get("text") or "").lower().strip()
        if not text:
            return
        for keywords, topic in self.RULES:
            if any(kw in text for kw in keywords):
                log.info("dispatch: '%s' → %s", text[:40], topic)
                event_log.append("dispatcher.routed",
                                 {"text": text[:80], "topic": topic},
                                 src=self.name)
                if self.ctx:
                    await self.ctx.bus.publish(topic, {"text": text})
                return
        # WANDER_DISPATCH_QUIET_V1: не спамим вслух.
        # Только лог. Fallback говорить — только если явно позвали "Аура".
        log.info("dispatch: no rule for '%s'", text[:40])
        event_log.append("dispatcher.no_match",
                         {"text": text[:80]}, src=self.name)
        # WANDER_NO_FALLBACK_V2: не отвечаем вслух. Только лог.

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "version": self.version,
                "rules": len(self.RULES)}

    async def stop(self) -> None:
        self._running = False
        if self.ctx:
            for h in list(self.ctx.bus._subs.get("voice.heard", [])):
                self.ctx.bus.unsubscribe("voice.heard", h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
