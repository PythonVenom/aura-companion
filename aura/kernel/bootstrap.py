"""Aura Bootstrap — единая точка входа для ядра.
Собирает: bus + registry + supervisor + router + агенты.
Наука: Composition Root (Seemann), Bootstrap Pattern (Fowler).
"""
import asyncio
import logging

from aura.contracts.agent import AgentContext
from aura.kernel.bus import bus
from aura.kernel.log import event_log
from aura.kernel.registry import registry
from aura.kernel.router import Router
from aura.kernel.supervisor import Supervisor

log = logging.getLogger("aura.bootstrap")


class AuraKernel:
    """Живой организм Aura. Одна точка входа."""

    def __init__(self):
        self.bus = bus
        self.registry = registry
        self.sup = Supervisor(bus, registry)
        self.router = Router(bus)
        self.ctx = AgentContext(bus=bus, capabilities=[], log=event_log)
        self._tasks = []

    def _make_factory(self, agent_class):
        """Фабрика: создаёт агента, стартует, живёт вечно."""
        async def _factory():
            agent = agent_class()
            await agent.start(self.ctx)
            while True:
                await asyncio.sleep(3600)
        return _factory

    def register_default_agents(self):
        """Регистрация мигрированных агентов + правил router."""
        from aura.kernel.agents.audio_ducker import AudioDuckerAgent
        from aura.kernel.agents.calendar import CalendarAgent
        from aura.kernel.agents.care import CareAgent
        from aura.kernel.agents.cleaner import CleanerAgent
        from aura.kernel.agents.dispatcher import DispatcherAgent
        from aura.kernel.agents.email import EmailAgent
        from aura.kernel.agents.fall import FallAgent
        from aura.kernel.agents.max import MaxAgent
        from aura.kernel.agents.meds import MedsAgent
        from aura.kernel.agents.mentor.agent import MentorAgent
        from aura.kernel.agents.obd import OBDAgent
        from aura.kernel.agents.proactive_alert import ProactiveAlertAgent
        from aura.kernel.agents.smarthome import SmartHomeAgent
        from aura.kernel.agents.sos import SOSAgent
        
        from aura.kernel.agents.stop_control import StopControlAgent
        from aura.kernel.agents.telegram import TelegramAgent
        from aura.kernel.agents.time import TimeAgent
        from aura.kernel.agents.vk import VKAgent
        from aura.kernel.agents.voice import VoiceAgent
        from aura.kernel.agents.weather import WeatherAgent
        from aura.kernel.agents.whatsapp import WhatsAppAgent

        # Агенты
        self.sup.spawn("time", self._make_factory(TimeAgent))
        pass # SpeakerAgent disabled
        self.sup.spawn("meds", self._make_factory(MedsAgent))
        self.sup.spawn("fall", self._make_factory(FallAgent))
        self.sup.spawn("sos", self._make_factory(SOSAgent))
        self.sup.spawn("proactive_alert", self._make_factory(ProactiveAlertAgent))
        self.sup.spawn("voice", self._make_factory(VoiceAgent))
        self.sup.spawn("dispatcher", self._make_factory(DispatcherAgent))
        self.sup.spawn("audio_ducker", self._make_factory(AudioDuckerAgent))
        # self.sup.spawn("vision", self._make_factory(VisionAgent))  # AURA_CAMERA_OFF
        self.sup.spawn("calendar", self._make_factory(CalendarAgent))
        self.sup.spawn("mentor", self._make_factory(MentorAgent))
        self.sup.spawn("smarthome", self._make_factory(SmartHomeAgent))
        self.sup.spawn("stop_control", self._make_factory(StopControlAgent))
        self.sup.spawn("vk", self._make_factory(VKAgent))
        self.sup.spawn("max", self._make_factory(MaxAgent))
        self.sup.spawn("whatsapp", self._make_factory(WhatsAppAgent))
        self.sup.spawn("email", self._make_factory(EmailAgent))
        self.sup.spawn("telegram", self._make_factory(TelegramAgent))
        self.sup.spawn("cleaner", self._make_factory(CleanerAgent))
        self.sup.spawn("obd", self._make_factory(OBDAgent))
        self.sup.spawn("care", self._make_factory(CareAgent))
        self.sup.spawn("weather", self._make_factory(WeatherAgent))

        # Router — связи между агентами
        self.router.rule("time.answer", "speaker.say", text_key="time")
        self.router.rule("meds.reminder", "speaker.say", text_key="text")
        self.router.rule("meds.list_result", "speaker.say", text_key="text")
        self.router.rule("fall.detected", "sos.trigger", text_key="text")
        self.router.rule("sos.answer", "speaker.say", text_key="text")
        self.router.rule("proactive.alert", "sos.trigger", text_key="text")
        self.router.rule("proactive.alert", "speaker.say", text_key="text")

        # T-020: calendar.answer → speaker
        self.router.rule("calendar.answer", "speaker.say", text_key="text")

        # T-021: care.reminder → speaker
        self.router.rule("care.reminder", "speaker.say", text_key="text")
        self.router.rule("care.answer", "speaker.say", text_key="text")
        self.router.rule("care.greeting", "speaker.say", text_key="text")

        # T-022: weather.answer → speaker
        self.router.rule("weather.answer", "speaker.say", text_key="text")
        self.router.rule("mentor.answer", "speaker.say", text_key="text")

        # T-025: vision.motion — только лог, не говорим (шум)
        self.router.rule("voice.heard", "dispatcher.dispatch", text_key="text")

        log.info("kernel: 21 agents + 12 router rules")
        event_log.append("kernel.bootstrapped",
                         {"agents": list(self.registry.all().keys()),
                          "rules": len(self.router._rules)},
                         src="bootstrap")

    async def start(self):
        """Запустить всё: bus + agents."""
        self.register_default_agents()
        bus_task = asyncio.create_task(self.bus.run(), name="bus")
        self._tasks.append(bus_task)
        log.info("kernel started")

    async def stop(self):
        await self.sup.shutdown()
        for t in self._tasks:
            t.cancel()
        log.info("kernel stopped")

    def status(self) -> dict:
        return {
            "organs": self.registry.all(),
            "rules": [f"{a}->{b}" for a, b in self.router._rules],
        }
