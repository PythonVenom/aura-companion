"""AgentDataMiner — сбор данных: цены, курсы, погода, факты.

Сканирует внешние источники (открытые API) и возвращает структурированные данные.
Лор: AURA добывает данные из инфокосмоса.

Наука: Web Scraping (Mitchell 2018), ETL pipelines.
"""
from __future__ import annotations

import json
import urllib.request
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentDataMiner(BaseAgent):
    """Добывает данные из внешних источников."""

    name = "data_miner"
    MODULE_ALWAYS = True

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(k in t for k in (
            "собери данные", "добудь", "получи данные",
            "сколько сейчас", "цена", "стоимость",
        ))

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        t = request.text.lower()
        # Заглушка: возвращаем структуру (реальные API — задел)
        if "курс" in t or "доллар" in t or "евро" in t:
            return AgentResponse.ok(
                text="🛸 Данные: курс валют — запроси у AgentFinElder (живой ЦБ РФ).",
                agent_name=self.name,
            )
        return AgentResponse.ok(
            text="🛸 DataMiner готов. Уточни: 'цена', 'курс', 'стоимость'.",
            agent_name=self.name,
        )


__all__ = ["AgentDataMiner"]
