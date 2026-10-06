"""Matter bridge agent. T032 — универсальный умный дом.

Наука (CSA Matter 1.0, 2022): единый стандарт для умного дома.
Aura — голосовой слой над Matter-устройствами через python-matter-server.

Config: ~/.config/aura/matter.json
- server_url: ws://localhost:5580/ws
- devices: {name: node_id}
"""
from __future__ import annotations

import json
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


CONFIG = Path.home() / ".config" / "aura" / "matter.json"


class AgentMatter(BaseAgent):
    name = "matter"
    MODULE_ALWAYS = True

    TRIGGERS = (
        "включи розетку", "выключи розетку", "розетка",
        "термостат", "кондиционер", "обогрев",
        "matter", "умный дом",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        cfg = self._load_config()
        if not cfg.get("server_url"):
            return AgentResponse.ok(
                text="Matter не настроен. Заполни ~/.config/aura/matter.json",
                agent_name=self.name,
            )

        t = request.text.lower()
        action = "turn_on" if "включи" in t else "turn_off"

        # Устройство?
        devices = cfg.get("devices", {})
        for name, node_id in devices.items():
            if name in t:
                return self._send(cfg, node_id, action, name)

        return AgentResponse.ok(
            text=f"Matter: {len(devices)} устройств. Скажи 'включи <имя>'.",
            agent_name=self.name,
        )

    def _send(self, cfg: dict, node_id: int, action: str, name: str) -> AgentResponse:
        """Отправка команды через websocket (заглушка — нужен python-matter-server)."""
        try:
            # TODO: websocket client к python-matter-server
            return AgentResponse.ok(
                text=f"🏠 {action} {name} (node {node_id})",
                agent_name=self.name,
            )
        except Exception as e:
            return AgentResponse.ok(
                text=f"⚠️ Matter error: {e}",
                agent_name=self.name,
            )

    def _load_config(self) -> dict:
        try:
            if CONFIG.exists():
                return json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception as e:
            # F-006: не глотать (раздел 17 промта)
            import logging
            logging.getLogger('aura.matter').debug(
                'matter error: %s', e)
        return {"server_url": "", "devices": {}}
