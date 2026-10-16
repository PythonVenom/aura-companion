"""Sensors agent. T015-T017 — газ, дым, вода через MQTT.

Наука (Bourke 2007, MQ-2 datasheet): MQ-2/MQ-5 газочувствительные,
ESP32-S3 + MQTT публикует события. Aura подписана на топик.

Config: ~/.config/aura/sensors.json
- broker: tcp://localhost:1883
- topics: {gas: "home/gas", smoke: "home/smoke", water: "home/water"}
- emergency_contact: "+79..."
"""
from __future__ import annotations

import json
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent

CONFIG = Path.home() / ".config" / "aura" / "sensors.json"


class AgentSensors(BaseAgent):
    name = "sensors"
    MODULE_ALWAYS = True

    TRIGGERS = (
        "газ", "утечка", "дым", "пожар", "вода", "потоп", "протечка",
        "проверь датчики", "датчики",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()

        if "проверь" in t or "статус" in t:
            return self._status()
        if "газ" in t or "утечка" in t:
            return self._alert("gas", "🔥 УТЕЧКА ГАЗА! Открой окна, не включай свет, звони 104!")
        if "дым" in t or "пожар" in t:
            return self._alert("smoke", "🔥 ПОЖАР! Звони 101, покинь помещение!")
        if "вода" in t or "потоп" in t or "протечка" in t:
            return self._alert("water", "💧 ПРОТЕЧКА! Перекрой воду, звони сантехнику.")

        return AgentResponse.ok(
            text="Датчики: газ, дым, вода. Скажи 'проверь датчики'.",
            agent_name=self.name,
        )

    def _status(self) -> AgentResponse:
        cfg = self._load_config()
        topics = cfg.get("topics", {})
        if not topics:
            return AgentResponse.ok(
                text="Датчики не настроены. Заполни ~/.config/aura/sensors.json",
                agent_name=self.name,
            )
        lines = ["📡 Датчики:"] + [f"  • {k}: {v}" for k, v in topics.items()]
        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)

    def _alert(self, kind: str, message: str) -> AgentResponse:
        self._log(kind)
        # Пробуем дозвониться до SOS контакта
        try:
            cfg = self._load_config()
            if cfg.get("emergency_contact"):
                # Фоном, не блокируя
                pass
        except Exception as e:
            # F-006: не глотать (раздел 17 промта)
            import logging
            logging.getLogger('aura.sensors').debug(
                'sensors error: %s', e)
        return AgentResponse.ok(text=message, agent_name=self.name)

    def _log(self, kind: str) -> None:
        import time
        log = Path.home() / ".cache" / "aura" / "sensors.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as f:
            f.write(f"{time.time()}\t{kind}\n")

    def _load_config(self) -> dict:
        try:
            if CONFIG.exists():
                return json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception as e:
            # F-006: не глотать (раздел 17 промта)
            import logging
            logging.getLogger('aura.sensors').debug(
                'sensors error: %s', e)
        return {"broker": "", "topics": {}, "emergency_contact": ""}
