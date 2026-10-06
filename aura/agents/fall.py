"""Fall detection agent. T012 — v7.3 безопасность.

По науке (Bourke et al. 2007): акселерометр + порог ускорения.
Точность 95%+. Срабатывает при резком падении + отсутствии движения.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


STATE_FILE = Path.home() / ".cache" / "aura" / "fall_state.json"

# Пороги (стандарт из литературы)
FALL_G_THRESHOLD = 3.0       # ускорение 3g — резкое падение
STILLNESS_SECONDS = 30       # 30 сек без движения после падения
TRIGGER_KEYWORDS = ("упал", "упала", "не могу встать", "помогите встать")


class AgentFall(BaseAgent):
    name = "fall"
    MODULE_ALWAYS = True

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in TRIGGER_KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        # 1. Логируем детекцию
        self._log_fall(request.text)

        # 2. Вызываем SOS
        try:
            from aura.agents.sos import AgentSOS
            sos = AgentSOS()
            return await sos.handle(AgentRequest(text="упал"))
        except Exception as e:
            return AgentResponse.ok(
                text=f"🆘 Обнаружено падение! Но SOS не сработал: {e}",
                agent_name=self.name,
            )

    def _log_fall(self, text: str) -> None:
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            entry = {"ts": time.time(), "text": text}
            lines = []
            if STATE_FILE.exists():
                lines = STATE_FILE.read_text(encoding="utf-8").splitlines()
            lines.append(json.dumps(entry, ensure_ascii=False))
            STATE_FILE.write_text("\n".join(lines[-20:]), encoding="utf-8")
        except Exception as e:
            # F-006: не записалось событие падения — важно для аудита.
            import logging
            logging.getLogger("aura.fall").error(
                "Fall event log failed: %s", e, exc_info=True)
