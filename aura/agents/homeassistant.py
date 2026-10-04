"""HomeAssistant agent. T033+T034 — умный дом.

Через REST API HA (https://www.home-assistant.io/integrations/http/).
Config: ~/.config/aura/homeassistant.json
- url: http://homeassistant.local:8123
- token: long-lived-access-token
- lights: {name: entity_id}
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


CONFIG = Path.home() / ".config" / "aura" / "homeassistant.json"


class AgentHomeAssistant(BaseAgent):
    name = "homeassistant"
    MODULE_ALWAYS = True

    TRIGGERS = (
        "включи свет", "выключи свет", "свет в", "свет в комнате",
        "лампа", "включи лампу", "выключи лампу",
        "умный дом", "включи розетку", "выключи розетку",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        cfg = self._load_config()
        if not cfg.get("url") or not cfg.get("token"):
            return AgentResponse.ok(
                text="Умный дом не настроен. Заполни ~/.config/aura/homeassistant.json",
                agent_name=self.name,
            )

        t = request.text.lower()
        action = "turn_on" if "включи" in t else "turn_off"

        # Комната?
        room = self._extract_room(t)
        if room:
            entity = cfg.get("lights", {}).get(room)
            if not entity:
                return AgentResponse.ok(
                    text=f"Комната {room} не настроена",
                    agent_name=self.name,
                )
            return self._call(cfg, "light", action, entity)

        # Все лампы
        return self._call(cfg, "light", action, "all")

    def _extract_room(self, t: str) -> str | None:
        for kw in ("свет в ", "лампа в ", "свет в комнате "):
            if kw in t:
                rest = t.split(kw, 1)[1].strip().split()[0] if len(t.split(kw, 1)[1].strip().split()) > 0 else ""
                return rest
        return None

    def _call(self, cfg: dict, domain: str, service: str, target: str) -> AgentResponse:
        url = cfg["url"].rstrip("/") + f"/api/services/{domain}/{service}"
        try:
            data = json.dumps({"entity_id": target}).encode("utf-8")
            req = urllib.request.Request(
                url, data=data,
                headers={
                    "Authorization": f"Bearer {cfg['token']}",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                _ = r.read()
            icon = "💡" if service == "turn_on" else "🌑"
            return AgentResponse.ok(
                text=f"{icon} {service} {target}",
                agent_name=self.name,
            )
        except Exception as e:
            return AgentResponse.ok(
                text=f"⚠️ HA error: {e}",
                agent_name=self.name,
            )

    def _load_config(self) -> dict:
        try:
            if CONFIG.exists():
                return json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {"url": "", "token": "", "lights": {}}
