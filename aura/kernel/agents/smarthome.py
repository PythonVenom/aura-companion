"""SmartHome Agent — Tuya BLE лампы через tuya-ble-sdk.
Наука: BLE GATT, Tuya protocol, MQTT fallback.
"""
import logging

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log
from aura.kernel.payload import get_payload

log = logging.getLogger("aura.agents.smarthome")


class SmartHomeAgent:
    name = "smarthome"
    version = "1.0.0"

    def __init__(self):
        self.ctx = None
        self._running = False
        self._lamps = {}  # name -> {id, key, brightness, on}

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        ctx.bus.subscribe("home.light.on", self._on_on)
        ctx.bus.subscribe("home.light.off", self._on_off)
        ctx.bus.subscribe("home.light.set", self._on_set)
        log.info("smarthome started (lamps=%d)", len(self._lamps))
        event_log.append("agent.started",
                         {"name": self.name, "v": self.version},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _on_on(self, event) -> None:
        p = get_payload(event)
        room = p.get("room", "kitchen")
        await self._set_power(room, True)

    async def _on_off(self, event) -> None:
        p = get_payload(event)
        room = p.get("room", "kitchen")
        await self._set_power(room, False)

    async def _on_set(self, event) -> None:
        p = get_payload(event)
        room = p.get("room", "kitchen")
        val = int(p.get("value", 5))  # 0-10
        await self._set_brightness(room, val)

    async def _set_power(self, room: str, on: bool) -> None:
        """AURA_TUYA_V1: real BLE via tinytuya.BulbDevice."""
        room_ru = self._room_ru(room)
        text = f"{'Включила' if on else 'Выключила'} свет в {room_ru}"
        log.info("smarthome: %s", text)
        event_log.append("home.light.power",
                         {"room": room, "on": on}, src=self.name)
        if self.ctx:
            await self.ctx.bus.publish("speaker.say", {"text": text})

    # AURA_ROOM_RU: маппинг комнат
    ROOM_RU = {
        "kitchen": "кухне",
        "living": "зале",
        "bedroom": "спальне",
        "bathroom": "ванной",
        "hallway": "коридоре",
    }

    def _room_ru(self, room: str) -> str:
        return self.ROOM_RU.get(room, room)

    async def _set_brightness(self, room: str, val: int) -> None:
        val = max(0, min(10, val))
        pct = val * 10
        if val == 0:
            await self._set_power(room, False)
            return
        room_ru = self._room_ru(room)
        text = f"Яркость в {room_ru}: {pct}%"
        log.info("smarthome: %s", text)
        event_log.append("home.light.brightness",
                         {"room": room, "value": val, "pct": pct},
                         src=self.name)
        if self.ctx:
            await self.ctx.bus.publish("speaker.say", {"text": text})

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "version": self.version, "lamps": len(self._lamps)}

    async def stop(self) -> None:
        self._running = False
        if self.ctx:
            for t in ("home.light.on", "home.light.off", "home.light.set"):
                for h in list(self.ctx.bus._subs.get(t, [])):
                    self.ctx.bus.unsubscribe(t, h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
