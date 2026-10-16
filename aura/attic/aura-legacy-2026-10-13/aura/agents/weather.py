"""AgentWeather — погода для elder-care.

Понимает:
  - «какая погода» / «погода сейчас»
  - «погода на завтра»
  - «погода на неделю»

Источник: wttr.in (бесплатно, без ключа).
"""
from __future__ import annotations

import urllib.parse
import urllib.request

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentWeather(BaseAgent):
    """Погода — elder-care критично."""

    name = "weather"
    MODULE_NAME = "weather"

    TRIGGERS = ("погода", "прогноз", "дождь ли", "снег ли",
                "холодно ли", "тепло ли", "жарко ли",
                "ветер ли", "градус", "на улице")

    # Город — по умолчанию. Батя может поменять через конфиг.
    CITY = "Moscow"
    TIMEOUT = 8

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        if not any(kw in t for kw in self.TRIGGERS):
            return False
        # Не ловим календарные «напомни ...»
        return "напомни" not in t and "запиши" not in t

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()
        # AURA_WEATHER_ADVICE_ROUTE_V1
        if "надеть" in t or "одеть" in t or "одеться" in t:
            return self._advice()
        if "недел" in t:
            return self._forecast(days=7, label="на неделю")
        if "завтра" in t or "послезавтра" in t:
            return self._forecast(days=2, label="на завтра")
        return self._current()

    def _current(self) -> AgentResponse:
        """AURA_WEATHER_CURRENT_V2: по-русски, 'за бортом X'."""
        try:
            raw = self._fetch_simple()
            parts = [x.strip() for x in raw.split("|")]
            temp_str = parts[0] if len(parts) > 0 else "?"
            desc = parts[1] if len(parts) > 1 else ""
            temp_int = self._parse_temp(temp_str)
            if temp_int is not None:
                text = f"Сейчас за бортом {temp_int} градусов."
            else:
                text = f"Сейчас {temp_str}."
            if desc:
                text += f" {desc}."
            return AgentResponse.ok(text=text, agent_name=self.name)
        except Exception as e:
            return AgentResponse.ok(
                text=f"Не могу узнать погоду: {e}",
                agent_name=self.name,
            )

    def _advice(self) -> AgentResponse:
        """AURA_WEATHER_ADVICE_V2: рекомендация что надеть."""
        try:
            raw = self._fetch_simple()
            parts = [x.strip() for x in raw.split("|")]
            temp_int = self._parse_temp(parts[0]) if parts else None
            if temp_int is None:
                return AgentResponse.ok(
                    text="Не могу определить температуру.",
                    agent_name=self.name,
                )
            advice = self._clothing_advice(temp_int)
            text = f"Сейчас {temp_int}°. {advice}"
            return AgentResponse.ok(text=text, agent_name=self.name)
        except Exception as e:
            return AgentResponse.ok(
                text=f"Совет недоступен: {e}",
                agent_name=self.name,
            )

    def _forecast(self, days: int, label: str) -> AgentResponse:
        """AURA_WEATHER_FORECAST_V2: fast path через _fetch_forecast_simple."""
        try:
            raw = self._fetch_forecast_simple()
            lines = [f"📅 Погода {label}:"]
            for line in raw.splitlines()[:days]:
                lines.append(f"  {line.strip()}")
            if len(lines) == 1:
                return AgentResponse.ok(
                    text="Прогноз пуст.", agent_name=self.name)
            return AgentResponse.ok(text="\n".join(lines),
                                    agent_name=self.name)
        except Exception as e:
            return AgentResponse.ok(
                text=f"Не могу получить прогноз: {e}",
                agent_name=self.name)

    def _forecast_old(self, days: int, label: str) -> AgentResponse:
        try:
            data = self._fetch()
            forecast = data.get("weather", [])[:days]
            if not forecast:
                return AgentResponse.ok(
                    text="Прогноз пуст.",
                    agent_name=self.name,
                )
            lines = []
            for i, day in enumerate(forecast):
                date = day["date"]  # YYYY-MM-DD
                tmin = day["mintempC"]
                tmax = day["maxtempC"]
                # Описание дня — из полуденного часа
                hourly = day.get("hourly", [])
                desc = ""
                if hourly:
                    mid = hourly[len(hourly) // 2]
                    if mid.get("weatherDesc"):
                        desc = mid["weatherDesc"][0]["value"]
                if i == 0:
                    day_label = "сегодня"
                elif i == 1:
                    day_label = "завтра"
                else:
                    day_label = date[5:]  # MM-DD
                d = f" {desc}" if desc else ""
                lines.append(f"{day_label}: {tmin}..{tmax}°{d}")
            return AgentResponse.ok(
                text=f"Прогноз {label}: " + "; ".join(lines),
                agent_name=self.name,
            )
        except Exception as e:
            return AgentResponse.ok(
                text=f"Не могу получить прогноз: {e}",
                agent_name=self.name,
            )

    def _fetch(self) -> dict:
        """AURA_WEATHER_J1_V1: полный прогноз (j1) — долгий, timeout 20."""
        import requests
        city = urllib.parse.quote(self.CITY)
        url = f"https://wttr.in/{city}?format=j1"
        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise RuntimeError(
                f"прогноз недоступен ({type(e).__name__})") from e

    def _fetch_simple(self, retries: int = 2) -> str:
        """AURA_WEATHER_SIMPLE_V2: быстрый запрос + retry + lang=ru.
        format=%t|%C|%w — темп | описание | ветер.
        """
        import requests
        city = urllib.parse.quote(self.CITY)
        url = f"https://wttr.in/{city}?format=%t|%C|%w&lang=ru"
        last_err = None
        for attempt in range(retries + 1):
            try:
                r = requests.get(url, timeout=8)
                r.raise_for_status()
                return r.text.strip()
            except Exception as e:
                last_err = e
                if attempt < retries:
                    import time as _t
                    _t.sleep(0.5)
        raise RuntimeError(
            f"погода недоступна ({type(last_err).__name__})") from last_err

    def _fetch_forecast_simple(self) -> str:
        """AURA_WEATHER_FORECAST_V1: прогноз на 2 дня по-русски.
        format=%t|%C — только температура и описание для завтра/послезавтра.
        """
        import requests
        city = urllib.parse.quote(self.CITY)
        # %t — temp, %C — condition. Два дня через \n
        url = f"https://wttr.in/{city}?format=%t|%C&lang=ru"
        try:
            r = requests.get(url, timeout=8)
            r.raise_for_status()
            return r.text.strip()
        except Exception as e:
            raise RuntimeError(
                f"прогноз недоступен ({type(e).__name__})") from e

    @staticmethod
    def _clothing_advice(temp_c: int) -> str:
        """AURA_WEATHER_ADVICE_V1: что надеть по температуре."""
        if temp_c <= -15:
            return "Очень холодно. Пуховик, шапка, шарф, перчатки."
        if temp_c <= -5:
            return "Морозно. Зимняя куртка, шапка, перчатки."
        if temp_c <= 0:
            return "Мороз. Тёплая куртка, шапка, перчатки."
        if temp_c <= 8:
            return "Прохладно. Куртка, шапка."
        if temp_c <= 15:
            return "Свежо. Лёгкая куртка или свитер."
        if temp_c <= 22:
            return "Тепло. Футболка, лёгкая кофта."
        if temp_c <= 28:
            return "Жарко. Лёгкая одежда."
        return "Очень жарко. Футболка, панама, вода."

    @staticmethod
    def _parse_temp(s: str) -> int | None:
        """'+13°C' → 13. '−3°C' → -3."""
        import re
        m = re.search(r"([+-]?\d+)", s.replace("−", "-"))
        return int(m.group(1)) if m else None

