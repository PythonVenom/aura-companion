"""FinElder agent. T026-T030 — финансовый помощник для пожилых.

Только информация и напоминания. НЕ делает переводы, НЕ даёт
инвестиционных советов. Disclaimer: не медизделие, не банк.

Данные:
- cbr-xml-daily.ru — курсы ЦБ РФ (без API ключа)
- config: ~/.config/aura/fin_elder.json
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


CONFIG = Path.home() / ".config" / "aura" / "fin_elder.json"
CBR_URL = "https://www.cbr-xml-daily.ru/daily_json.js"


class AgentFinElder(BaseAgent):
    name = "fin_elder"
    MODULE_ALWAYS = True

    TRIGGERS = (
        "курс", "доллар", "евро", "валюта", "цб",
        "жкх", "коммуналк", "оплатить", "оплата",
        "пенси", "мошенник", "обман", "звонят из банка",
        "антискам", "проверь счёт",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()

        if any(k in t for k in ("курс", "доллар", "евро", "валюта", "цб")):
            return self._currency()
        if any(k in t for k in ("жкх", "коммуналк")):
            return self._utilities()
        if any(k in t for k in ("пенси",)):
            return self._pension_reminder()
        if any(k in t for k in ("мошенник", "обман", "звонят из банка", "антискам")):
            return self._scam_warning()

        return self._status()

    def _currency(self) -> AgentResponse:
        try:
            with urllib.request.urlopen(CBR_URL, timeout=5) as r:
                data = json.loads(r.read().decode("utf-8"))
            usd = data["Valute"]["USD"]["Value"]
            eur = data["Valute"]["EUR"]["Value"]
            return AgentResponse.ok(
                text=f"💵 Курс ЦБ: доллар {usd:.2f} ₽, евро {eur:.2f} ₽",
                agent_name=self.name,
            )
        except Exception as e:
            return AgentResponse.ok(
                text=f"Не могу получить курс ЦБ: {e}",
                agent_name=self.name,
            )

    def _utilities(self) -> AgentResponse:
        cfg = self._load_config()
        period = cfg.get("utility_period", "20-25")
        return AgentResponse.ok(
            text=f"📋 Оплата ЖКХ обычно {period} числа. "
                 f"Напомню за день до этого.",
            agent_name=self.name,
        )

    def _pension_reminder(self) -> AgentResponse:
        cfg = self._load_config()
        day = cfg.get("pension_day", 8)
        return AgentResponse.ok(
            text=f"📅 Пенсия обычно приходит {day}-го числа. Напомню.",
            agent_name=self.name,
        )

    def _scam_warning(self) -> AgentResponse:
        return AgentResponse.ok(
            text=(
                "⚠️ ВАЖНО: если звонят из банка и просят код или деньги — "
                "это МОШЕННИКИ. Настоящий банк никогда не спросит код. "
                "Повесь трубку и позвони сыну."
            ),
            agent_name=self.name,
        )

    def _status(self) -> AgentResponse:
        return AgentResponse.ok(
            text="FinElder готов. Спроси: 'курс доллара', 'оплата ЖКХ', "
                 "'пенсия', 'мошенники'.",
            agent_name=self.name,
        )

    def _load_config(self) -> dict:
        try:
            if CONFIG.exists():
                return json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {"pension_day": 8, "utility_period": "20-25"}
