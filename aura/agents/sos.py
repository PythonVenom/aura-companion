"""SOS agent — экстренный вызов. T011."""
from __future__ import annotations
import json
import subprocess
import time
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


CONFIG = Path.home() / ".config" / "aura" / "sos.json"


class AgentSOS(BaseAgent):
    name = "sos"
    MODULE_ALWAYS = True

    # Триггеры: SOS фразы
    # AURA_SOS_BT_V1 — расширенные триггеры (включая BT-кнопку)
    SOS_PHRASES = (
        "мне плохо", "помогите", "вызови скорую", "вызов скорой",
        "плохо мне", "срочно помогите", "вызови помощь",
        "sos", "сос", "упал", "упала", "не могу встать",
        "тревога", "плохо с сердцем", "вызови сына", "вызови дочь",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower().strip()
        # AURA_SOS_CONTACT_V1 — установка контакта
        if "установи sos" in t or "sos контакт" in t:
            return True
        return any(p in t for p in self.SOS_PHRASES)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        cfg = self._load_config()
        contact = cfg.get("contact", "")

        if not contact:
            return AgentResponse.ok(
                text="SOS! Но экстренный контакт не настроен. "
                     "Скажи: 'Аура, установи SOS контакт +79...'",
                agent_name=self.name,
            )

        # Логируем
        self._log_sos(request.text)

        # Пробуем позвонить через Telegram
        try:
            from aura.agents.telegram import AgentTelegram
            tg = AgentTelegram()
            await tg.handle(AgentRequest(text=f"позвони {contact}"))
            return AgentResponse.ok(
                text=f"🆘 SOS! Звоню {contact}",
                agent_name=self.name,
            )
        except Exception as e:
            return AgentResponse.ok(
                text=f"🆘 SOS! Не смогла позвонить ({e}). "
                     f"Набери {contact} вручную.",
                agent_name=self.name,
            )

    def _load_config(self) -> dict:
        try:
            if CONFIG.exists():
                return json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception as e:
            # F-006: SOS не может прочитать контакты — warning,
            # fallback на пустой config (дальше сработает manual).
            import logging
            logging.getLogger("aura.sos").warning(
                "SOS config load failed: %s — fallback to manual", e)
        return {}

    def _log_sos(self, text: str) -> None:
        log = Path.home() / ".cache" / "aura" / "sos.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as f:
            f.write(f"{time.time()}\t{text}\n")
