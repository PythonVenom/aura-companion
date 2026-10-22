"""#133 AgentMQTT — управление умным домом через MQTT.

Наука:
- MQTT 5.0 (OASIS 2019) — publish/subscribe, QoS 0/1/2
- Hohpe & Woolf 2003 (EIP) — message bus
- Home Assistant MQTT Discovery — auto-detect устройств

Зачем:
  Прямая интеграция с Zigbee2MQTT, Tasmota, ESPHome, Home Assistant.
  Aura → MQTT broker → умные устройства (свет, розетки, датчики).

Настройки:
  ~/.config/aura/mqtt.json — broker, port, user, password, prefix.
"""
from __future__ import annotations

import json
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent

CONFIG_PATH = Path.home() / ".config/aura/mqtt.json"

try:
    import paho.mqtt.client as mqtt_client
    PAHO_OK = True
except ImportError:
    PAHO_OK = False
    mqtt_client = None


class AgentMQTT(BaseAgent):
    """Управление умным домом через MQTT."""

    name = "mqtt"

    TRIGGERS = (
        "включи mqtt", "выключи mqtt", "mqtt устройство",
        "mqtt статус", "умный дом mqtt", "mqtt список",
    )

    def __init__(self) -> None:
        super().__init__()
        self.config = self._load_config()
        self.client = None

    def _load_config(self) -> dict:
        if not CONFIG_PATH.exists():
            return {"broker": "localhost", "port": 1883,
                    "user": "", "password": "", "prefix": "aura"}
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {"broker": "localhost", "port": 1883,
                    "user": "", "password": "", "prefix": "aura"}

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not PAHO_OK:
            return AgentResponse.ok(
                "⚠️ paho-mqtt не установлен: pip install paho-mqtt",
                self.name,
            )
        t = request.text.lower()
        if "статус" in t or "список" in t:
            return AgentResponse.ok(self._status(), self.name)
        return AgentResponse.ok(
            f"MQTT: broker={self.config['broker']}:{self.config['port']}",
            self.name,
        )

    def _status(self) -> str:
        cfg = self.config
        return (
            f"📡 MQTT: {cfg['broker']}:{cfg['port']}\n"
            f"   prefix: {cfg['prefix']}\n"
            f"   user: {cfg['user'] or '(anon)'}\n"
            f"   paho: {'✅' if PAHO_OK else '❌'}"
        )

    def publish(self, topic: str, payload: str) -> bool:
        """Опубликовать сообщение (когда client запущен)."""
        if not self.client:
            return False
        try:
            self.client.publish(topic, payload)
            return True
        except Exception:
            return False


__all__ = ["CONFIG_PATH", "PAHO_OK", "AgentMQTT"]
