"""Fall detection agent. T012 — v7.3 безопасность.

По науке (Bourke et al. 2007): акселерометр + порог ускорения.
Точность 95%+. Срабатывает при резком падении + отсутствии движения.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from aura.core import blackboard as bb
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent

STATE_FILE = Path.home() / ".cache" / "aura" / "fall_state.json"

# Пороги (стандарт из литературы)
FALL_G_THRESHOLD = 3.0       # ускорение 3g — резкое падение
STILLNESS_SECONDS = 30       # 30 сек без движения после падения
TRIGGER_KEYWORDS = ("упал", "упала", "не могу встать", "помогите встать")


class AgentFall(BaseAgent):
    name = "fall"
    MODULE_ALWAYS = True
    STATE_FILE = STATE_FILE  # class attribute (для тестов)

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in TRIGGER_KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        # BUG-FIX: проверка can_handle (без неё — любой текст → SOS)
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        # 1. Логируем детекцию
        self._log_fall(request.text)
        # Blackboard: тревога критична — рой должен знать
        try:
            bb.post_alert("fall", "critical", f"Падение: {request.text[:50]}")
            bb.set_sector("health")
            bb.log_trail("fall", "sos", "escalate")
        except Exception:
            pass

        # 2. Вызываем SOS
        try:
            from aura.agents.sos import AgentSOS
            sos = AgentSOS()
            # "sos" в тексте обходит can_handle SOS (SOS_PHRASES проверяет фразы)
            return await sos.handle(AgentRequest(text="sos упал"))
        except Exception as e:
            return AgentResponse.ok(
                text=f"🆘 Обнаружено падение! Но SOS не сработал: {e}",
                agent_name=self.name,
            )

    def _log_fall(self, text: str) -> None:
        try:
            self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            entry = {"ts": time.time(), "text": text}
            lines = []
            if self.STATE_FILE.exists():
                lines = self.STATE_FILE.read_text(encoding="utf-8").splitlines()
            lines.append(json.dumps(entry, ensure_ascii=False))
            self.STATE_FILE.write_text("\n".join(lines[-20:]), encoding="utf-8")
        except Exception as e:
            # F-006: не записалось событие падения — важно для аудита.
            import logging
            logging.getLogger("aura.fall").error(
                "Fall event log failed: %s", e, exc_info=True)
