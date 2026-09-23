"""
Агент интернет-запросов.

Умеет:
- "погода в <город>" → погода через wttr.in
- "курс доллара" / "курс евро" → курс ЦБ РФ
- "что такое <запрос>" / "найди <запрос>" → Wikipedia RU

По науке:
- Изолирован (только HTTP-клиент)
- Тестируем (mock для requests)
- Не знает про AuraCore
- Без API-ключей (только публичные бесплатные API)
"""

from __future__ import annotations

import re
import urllib.parse
import urllib.request

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentInternet(BaseAgent):
    """
    Агент интернет-запросов.

    Обрабатывает:
    - "погода" / "погода в Москве" → wttr.in
    - "курс доллара" / "курс евро" → ЦБ РФ
    - "что такое X" / "кто такой X" / "найди X" → Wikipedia RU
    """

    name = "internet"
    MODULE_ALWAYS = True

    WEATHER_KEYWORDS = ("погода", "погоду", "weather")
    CURRENCY_KEYWORDS = ("курс", "доллар", "евро", "юань", "валюта")
    WIKI_KEYWORDS = ("что такое", "кто такой", "кто такая", "найди", "расскажи про")

    CURRENCY_CODES = {
        "доллар": "USD",
        "доллара": "USD",
        "евро": "EUR",
        "юань": "CNY",
        "юаня": "CNY",
        "фунт": "GBP",
        "фунта": "GBP",
    }

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        keywords = self.WEATHER_KEYWORDS + self.CURRENCY_KEYWORDS + self.WIKI_KEYWORDS
        return any(kw in text for kw in keywords)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        if any(kw in text for kw in self.WEATHER_KEYWORDS):
            city = self._extract_city(request.text)
            return AgentResponse.ok(self.get_weather(city), self.name)

        if any(kw in text for kw in self.CURRENCY_KEYWORDS):
            code = self._extract_currency(text)
            if code:
                return AgentResponse.ok(self.get_currency(code), self.name)
            return AgentResponse.ok(self.get_all_currencies(), self.name)

        if any(kw in text for kw in self.WIKI_KEYWORDS):
            query = self._extract_query(request.text)
            if query:
                return AgentResponse.ok(self.get_wiki(query), self.name)
            return AgentResponse.ok("Что найти?", self.name)

        return AgentResponse.not_handled(self.name)

    # --- Внутренние методы ---

    def _extract_city(self, text: str) -> str:
        """Извлечь город из 'погода в Москве'."""
        text = text.lower()
        for prep in (" в ", " во "):
            if prep in text:
                city = text.split(prep, 1)[1].strip()
                city = re.sub(r"[?.!]+$", "", city)
                return city
        # Убрать ключевое слово
        for kw in self.WEATHER_KEYWORDS:
            text = text.replace(kw, "")
        return text.strip() or "Moscow"

    def _extract_currency(self, text: str) -> str | None:
        for word, code in self.CURRENCY_CODES.items():
            if word in text:
                return code
        return None

    def _extract_query(self, text: str) -> str:
        text = text.lower()
        for kw in self.WIKI_KEYWORDS:
            if kw in text:
                query = text.split(kw, 1)[1].strip()
                query = re.sub(r"[?.!]+$", "", query)
                return query
        return ""

    def get_weather(self, city: str) -> str:
        """Погода через wttr.in (plain text, русский)."""
        try:
            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=%l:+%c+%t,+wind:+%w&lang=ru"
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read().decode("utf-8").strip()
            if not data or "Unknown" in data:
                return f"❌ Не нашла город: {city}"
            return f"🌤 Погода: {data}"
        except Exception as e:
            return f"❌ Не удалось получить погоду: {e}"

    def get_currency(self, code: str) -> str:
        """Курс валюты через ЦБ РФ."""
        try:
            url = "https://www.cbr-xml-daily.ru/daily_json.js"
            with urllib.request.urlopen(url, timeout=10) as resp:
                import json

                data = json.loads(resp.read().decode("utf-8"))
            val = data.get("Valute", {}).get(code)
            if not val:
                return f"❌ Курс для {code} не найден"
            value = val.get("Value", 0)
            nominal = val.get("Nominal", 1)
            per_unit = value / nominal
            return f"💱 1 {code} = {per_unit:.2f} ₽"
        except Exception as e:
            return f"❌ Не удалось получить курс: {e}"

    def get_all_currencies(self) -> str:
        """Все основные курсы."""
        try:
            url = "https://www.cbr-xml-daily.ru/daily_json.js"
            with urllib.request.urlopen(url, timeout=10) as resp:
                import json

                data = json.loads(resp.read().decode("utf-8"))
            lines = ["💱 Курсы ЦБ РФ:"]
            for code in ("USD", "EUR", "CNY"):
                val = data.get("Valute", {}).get(code)
                if val:
                    per_unit = val["Value"] / val.get("Nominal", 1)
                    lines.append(f"  1 {code} = {per_unit:.2f} ₽")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Не удалось получить курсы: {e}"

    def get_wiki(self, query: str) -> str:
        """Краткая справка из Wikipedia RU."""
        try:
            api = "https://ru.wikipedia.org/api/rest_v1/page/summary/"
            url = api + urllib.parse.quote(query)
            req = urllib.request.Request(url, headers={"User-Agent": "Aura/0.8"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                import json

                data = json.loads(resp.read().decode("utf-8"))
            extract = data.get("extract", "").strip()
            if not extract:
                return f"❌ Ничего не нашла по запросу: {query}"
            # Ограничить 500 символами
            if len(extract) > 500:
                extract = extract[:497] + "..."
            return f"📖 {extract}"
        except Exception as e:
            return f"❌ Не удалось найти: {e}"


__all__ = ["AgentInternet"]
