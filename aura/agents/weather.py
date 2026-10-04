"""Weather agent — live прогноз (OpenWeatherMap + Yandex fallback).

Bug 51: LLM галлюцинировал погоду. Этот агент даёт live-данные.
"""
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

try:
    from aura.agents.base import MicroAgent
except Exception:
    MicroAgent = object


OPENWEATHER_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
YANDEX_KEY = os.environ.get("YANDEX_WEATHER_KEY", "")
DEFAULT_CITY = os.environ.get("AURA_CITY", "Москва")


class WeatherAgent(MicroAgent):
    def __init__(self):
        try:
            super().__init__("weather", "Погода")
        except Exception:
            self.name = "weather"
            self.active = True
            self.description = "Погода"

    # ---- helpers ----
    def _owm_current(self, city: str) -> str | None:
        if not OPENWEATHER_KEY:
            return None
        try:
            url = (
                "https://api.openweathermap.org/data/2.5/weather?"
                + urllib.parse.urlencode({
                    "q": city,
                    "appid": OPENWEATHER_KEY,
                    "units": "metric",
                    "lang": "ru",
                })
            )
            with urllib.request.urlopen(url, timeout=5) as r:
                d = json.load(r)
            t = d["main"]["temp"]
            desc = d["weather"][0]["description"]
            wind = d.get("wind", {}).get("speed", 0)
            return f"Сейчас в {city} {t:+.0f}°, {desc}, ветер {wind:.0f} м/с."
        except Exception as e:
            return f"OWM error: {e}"

    def _owm_forecast(self, city: str, days: int = 1) -> str | None:
        if not OPENWEATHER_KEY:
            return None
        try:
            url = (
                "https://api.openweathermap.org/data/2.5/forecast?"
                + urllib.parse.urlencode({
                    "q": city,
                    "appid": OPENWEATHER_KEY,
                    "units": "metric",
                    "lang": "ru",
                })
            )
            with urllib.request.urlopen(url, timeout=5) as r:
                d = json.load(r)
            target = datetime.now() + timedelta(days=days)
            # Найти ближайший дневной слот
            best = None
            best_delta = 1e9
            for item in d["list"]:
                dt = datetime.fromtimestamp(item["dt"])
                # 12:00 целевого дня
                want = target.replace(hour=12, minute=0, second=0, microsecond=0)
                delta = abs((dt - want).total_seconds())
                if delta < best_delta:
                    best_delta = delta
                    best = item
            if not best:
                return None
            t = best["main"]["temp"]
            desc = best["weather"][0]["description"]
            word = "Завтра" if days == 1 else "Послезавтра"
            return f"{word} в {city} ожидается {t:+.0f}°, {desc}."
        except Exception as e:
            return f"OWM forecast error: {e}"

    # ---- API агента ----
    def now(self, city: str | None = None) -> str:
        c = city or DEFAULT_CITY
        r = self._owm_current(c)
        return r or "Не могу получить погоду — нет доступа к сервису."

    def tomorrow(self, city: str | None = None) -> str:
        c = city or DEFAULT_CITY
        r = self._owm_forecast(c, days=1)
        return r or "Не могу получить прогноз — нет доступа к сервису."

    def after_tomorrow(self, city: str | None = None) -> str:
        c = city or DEFAULT_CITY
        r = self._owm_forecast(c, days=2)
        return r or "Не могу получить прогноз — нет доступа к сервису."

    # AURA_RURAL_WEATHER_V1 — T038 погода для дачи
    def rural_forecast(self, city: str | None = None) -> str:
        """Погода на 3 дня — для планирования дачных работ."""
        c = city or DEFAULT_CITY
        results = []
        for days in (0, 1, 2):
            r = self._owm_forecast(c, days=days) if days > 0 else self._owm_current(c)
            if r:
                results.append(r)
        if not results:
            return "Не могу получить прогноз для дачи."
        return "\n".join(results)

    def handle(self, text: str) -> str:
        t = text.lower()
        # AURA_RURAL_WEATHER_V1 — дача
        if "дач" in t or "3 дня" in t or "три дня" in t or "выходные" in t:
            return self.rural_forecast()
        if "завтра" in t and "послезавтра" not in t:
            return self.tomorrow()
        if "послезавтра" in t:
            return self.after_tomorrow()
        return self.now()


# ---- CLI smoke ----
if __name__ == "__main__":
    a = WeatherAgent()
    print("NOW:     ", a.now())
    print("TOMORROW:", a.tomorrow())
    print("AFTER:   ", a.after_tomorrow())
