"""Weather agent — Open-Meteo (бесплатно, без ключа).

Bug 51: LLM галлюцинировал погоду. Этот агент даёт live-данные.
API: https://open-meteo.com — free, no key, UV + apparent_temperature.

Д4 (наука):
- Open-Meteo API: https://open-meteo.com/en/docs
- Wind chill: Environment Canada (2001), NOAA
- Heat index: Rothfusz (1979), NWS SR 90-23
- ISO 7730:2005, Fanger (1970) — одежда и комфорт
- WHO (2002) — Global Solar UV Index
"""
import json
import urllib.parse
import urllib.request

try:
    from aura.agents.base import MicroAgent
except Exception:
    MicroAgent = object


DEFAULT_CITY = "Москва"
# Координаты городов РФ (расширять по мере нужды)
CITY_COORDS = {
    "москва": (55.7558, 37.6173),
    "санкт-петербург": (59.9343, 30.3351),
    "спб": (59.9343, 30.3351),
    "питер": (59.9343, 30.3351),
    "новосибирск": (55.0084, 82.9357),
    "екатеринбург": (56.8389, 60.6057),
    "казань": (55.8304, 49.0661),
    "самара": (53.1959, 50.1002),
    "краснодар": (45.0355, 38.9753),
    "сочи": (43.5855, 39.7231),
    "владивосток": (43.1332, 131.9113),
}


class WeatherAgent(MicroAgent):
    def __init__(self):
        try:
            super().__init__("weather", "Погода")
        except Exception:
            self.name = "weather"
            self.active = True
            self.description = "Погода"

    # ---- helpers ----
    @staticmethod
    def _coords(city: str):
        key = city.lower().strip()
        return CITY_COORDS.get(key, CITY_COORDS["москва"])

    def _fetch(self, city: str, days: int = 1):
        lat, lon = self._coords(city)
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,weather_code,"
                       "wind_speed_10m,relative_humidity_2m",
            "daily": "temperature_2m_max,temperature_2m_min,uv_index_max,"
                     "weather_code",
            "timezone": "Europe/Moscow",
            "forecast_days": max(2, days + 1),
        }
        url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=8) as r:
            return json.load(r)

    @staticmethod
    def _weather_ru(code: int) -> str:
        if code == 0: return "ясно"
        if code in (1, 2): return "малооблачно"
        if code == 3: return "облачно"
        if code in (45, 48): return "туман"
        if code in (51, 53, 55, 56, 57): return "морось"
        if code in (61, 63, 65, 66, 67): return "дождь"
        if code in (71, 73, 75, 77): return "снег"
        if code in (80, 81, 82): return "ливень"
        if code in (85, 86): return "снегопад"
        if code in (95, 96, 99): return "гроза"
        return "переменно"

    @staticmethod
    def _elder_advice(t: float, feels: float, wind_kmh: float,
                      humidity: float, uv: float) -> str:
        """Совет для пожилого. ISO 7730, Fanger 1970, WHO 2002."""
        parts = []
        base = feels if abs(feels - t) >= 2 else t
        if base < 0:
            parts.append("очень холодно — шапка, перчатки, шарф")
        elif base < 10:
            parts.append("прохладно — тёплая куртка")
        elif base < 18:
            parts.append("свежо — лёгкая куртка")
        elif base < 25:
            parts.append("тепло — рубашка с длинным рукавом")
        elif base < 30:
            parts.append("жарко — футболка, пей воду")
        else:
            parts.append("очень жарко — не выходи днём, пей воду")
        if wind_kmh >= 20:
            parts.append("ветрено — одевайся плотнее")
        if humidity >= 70 and t >= 22:
            parts.append("душно — открой окно")
        if uv is not None and uv >= 6:
            parts.append("UV высокий — панама и очки")
        return ", ".join(parts)

    def _format_current(self, city: str, data: dict) -> str:
        cur = data["current"]
        t = cur["temperature_2m"]
        feels = cur["apparent_temperature"]
        wind_kmh = cur["wind_speed_10m"]
        humidity = cur["relative_humidity_2m"]
        desc = self._weather_ru(cur["weather_code"])
        uv = data.get("daily", {}).get("uv_index_max", [None])[0]
        advice = self._elder_advice(t, feels, wind_kmh, humidity, uv)
        feels_txt = f", ощущается как {feels:+.0f}°" if abs(feels - t) >= 2 else ""
        uv_txt = f" UV {uv:.0f}." if uv is not None and uv >= 3 else ""
        return (f"Сейчас в {city} {t:+.0f}°{feels_txt}, {desc}.{uv_txt} "
                f"{advice.capitalize()}.")

    def _format_day(self, city: str, data: dict, day: int = 1) -> str:
        d = data["daily"]
        try:
            t_max = d["temperature_2m_max"][day]
            t_min = d["temperature_2m_min"][day]
            code = d["weather_code"][day]
        except (IndexError, KeyError):
            return "Не могу получить прогноз."
        word = "Завтра" if day == 1 else "Послезавтра"
        return f"{word} в {city} {t_min:+.0f}°…{t_max:+.0f}°, {self._weather_ru(code)}."

    # ---- API агента ----
    def now(self, city: str | None = None) -> str:
        c = city or DEFAULT_CITY
        try:
            data = self._fetch(c, days=1)
            return self._format_current(c, data)
        except Exception as e:
            return f"Не могу получить погоду: {e}"

    def tomorrow(self, city: str | None = None) -> str:
        c = city or DEFAULT_CITY
        try:
            data = self._fetch(c, days=2)
            return self._format_day(c, data, day=1)
        except Exception as e:
            return f"Не могу получить прогноз: {e}"

    def after_tomorrow(self, city: str | None = None) -> str:
        c = city or DEFAULT_CITY
        try:
            data = self._fetch(c, days=3)
            return self._format_day(c, data, day=2)
        except Exception as e:
            return f"Не могу получить прогноз: {e}"

    def rural_forecast(self, city: str | None = None) -> str:
        c = city or DEFAULT_CITY
        try:
            data = self._fetch(c, days=3)
            lines = [self._format_current(c, data)]
            for d in (1, 2):
                lines.append(self._format_day(c, data, day=d))
            return "\n".join(lines)
        except Exception as e:
            return f"Не могу получить прогноз для дачи: {e}"

    def handle(self, text: str) -> str:
        t = text.lower()
        if "дач" in t or "3 дня" in t or "три дня" in t or "выходные" in t:
            return self.rural_forecast()
        if "завтра" in t and "послезавтра" not in t:
            return self.tomorrow()
        if "послезавтра" in t:
            return self.after_tomorrow()
        return self.now()


# ==== Наука (Д4) — референсы ====
# - Open-Meteo (2024). Free Weather API. https://open-meteo.com/en/docs
# - Environment Canada (2001). Wind Chill Index.
# - Rothfusz, L.P. (1979). The Heat Index Equation. NWS SR 90-23.
# - ISO 7730:2005. Ergonomics of the thermal environment.
# - Fanger, P.O. (1970). Thermal Comfort. Danish Technical Press.
# - WHO (2002). Global Solar UV Index: A Practical Guide.


if __name__ == "__main__":
    a = WeatherAgent()
    print("NOW:     ", a.now())
    print("TOMORROW:", a.tomorrow())
    print("AFTER:   ", a.after_tomorrow())
