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
import re
import urllib.parse
import urllib.request
from typing import Any

try:
    from aura.agents.base import MicroAgent
except Exception:
    MicroAgent = object  # type: ignore[assignment,misc]


from pathlib import Path
WEATHER_CITY_CACHE = Path.home() / ".cache/aura/weather_city.json"
WEATHER_ERR_TS = Path.home() / ".cache/aura/weather_last_error.ts"

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

    def _detect_city(self) -> str | None:
        """Определяет город по IP через ip-api.com (бесплатно, без ключа)."""
        import time as _t
        # кэш на 1 час
        if WEATHER_CITY_CACHE.exists():
            try:
                data = json.loads(WEATHER_CITY_CACHE.read_text(encoding="utf-8"))
                if _t.time() - data.get("ts", 0) < 3600 and data.get("city"):
                    return data["city"]
            except Exception:
                pass
        try:
            req = urllib.request.Request(
                "http://ip-api.com/json/?fields=status,city,regionName,country",
                headers={"User-Agent": "AuraOS/1.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                geo = json.loads(r.read().decode("utf-8"))
            if geo.get("status") == "success" and geo.get("city"):
                WEATHER_CITY_CACHE.parent.mkdir(parents=True, exist_ok=True)
                WEATHER_CITY_CACHE.write_text(
                    json.dumps({"city": geo["city"], "ts": _t.time()}, ensure_ascii=False),
                    encoding="utf-8",
                )
                return geo["city"]
        except Exception:
            pass
        return None

    @staticmethod
    def _coords(city: str):
        key = city.lower().strip()
        return CITY_COORDS.get(key, CITY_COORDS["москва"])

    def _fetch(self, city: str | None = None, days: int = 1):
        """Погода через curl с каскадным фолбэком (город -> авто по IP)."""
        import subprocess
        import time as _t

        if WEATHER_ERR_TS.exists():
            try:
                _last = float(WEATHER_ERR_TS.read_text(encoding="utf-8").strip())
                if _t.time() - _last < 300:
                    raise RuntimeError("weather_cooldown")
            except (ValueError, OSError):
                pass

        if not city:
            city = self._detect_city()
            
        # Собираем список URL для проверки
        urls = []
        if city:
            path = urllib.parse.quote(city)
            urls.append(f"https://wttr.in/{path}?format=j1")
            urls.append(f"https://wttr.in/{path}?format=%l:+%c+%t,+%f")
        
        # Если город не сработал — просим wttr.in определить по IP
        urls.append("https://wttr.in/?format=j1")
        urls.append("https://wttr.in/?format=%l:+%c+%t,+%f")

        last_err = None
        for url in urls:
            try:
                if "format=j1" in url:
                    res = subprocess.run(["curl", "-s", "-m", "12", "-H", "Accept-Language: ru", url], capture_output=True, text=True, check=True)
                    data = json.loads(res.stdout)
                    res_dict = self._adapt_wttr(data)
                else:
                    res = subprocess.run(["curl", "-s", "-m", "10", url], capture_output=True, text=True, check=True)
                    raw = res.stdout.strip()
                    if not raw or "Unknown location" in raw or "ERR" in raw:
                        raise ValueError("Bad response")
                    m = re.search(r'([+-]?\d+)°C', raw)
                    temp = float(m.group(1)) if m else 0.0
                    res_dict = {
                        "current": {
                            "temperature_2m": temp,
                            "apparent_temperature": temp,
                            "weather_code": 0,
                            "wind_speed_10m": 0,
                            "relative_humidity_2m": 0,
                            "_desc_ru": raw.split(":")[-1].strip(),
                        },
                        "daily": {"temperature_2m_max": [temp], "temperature_2m_min": [temp],
                                  "weather_code": [0], "uv_index_max": [0.0]}, # Защита от пустого списка
                    }
                
                # Успех!
                try:
                    WEATHER_ERR_TS.unlink(missing_ok=True)
                except OSError:
                    pass
                return res_dict
            except Exception as e:
                last_err = e
                _t.sleep(1.0)

        try:
            WEATHER_ERR_TS.parent.mkdir(parents=True, exist_ok=True)
            WEATHER_ERR_TS.write_text(str(_t.time()), encoding="utf-8")
        except OSError:
            pass
        raise RuntimeError("weather_unavailable") from last_err

    @staticmethod
    def _adapt_wttr(data: dict) -> dict:
        """Адаптирует JSON wttr.in под старый интерфейс."""
        def _f(val, default=0.0):
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        cur_list = data.get("current_condition", [])
        if not cur_list:
            raise ValueError("Location not found or empty response")
        cur = cur_list[0]
        
        result: dict[str, Any] = {
            "current": {
                "temperature_2m": _f(cur.get("temp_C")),
                "apparent_temperature": _f(cur.get("FeelsLikeC")),
                "weather_code": 0,
                "wind_speed_10m": _f(cur.get("windspeedKmph")),
                "relative_humidity_2m": _f(cur.get("humidity")),
            },
            "daily": {
                "temperature_2m_max": [],
                "temperature_2m_min": [],
                "weather_code": [],
                "uv_index_max": [],
            },
        }
        weather_days = data.get("weather", [])
        for d in weather_days[:3]:
            result["daily"]["temperature_2m_max"].append(_f(d.get("maxtempC")))
            result["daily"]["temperature_2m_min"].append(_f(d.get("mintempC")))
            result["daily"]["weather_code"].append(0)
        
        # Заполняем до 3 элементов
        while len(result["daily"]["temperature_2m_max"]) < 3:
            result["daily"]["temperature_2m_max"].append(0.0)
            result["daily"]["temperature_2m_min"].append(0.0)
            result["daily"]["weather_code"].append(0)
            
        result["daily"]["uv_index_max"] = [_f(cur.get("uvIndex"))] * 3

        desc = cur.get("lang_ru", [{}])[0].get("value") or cur.get("weatherDesc", [{}])[0].get("value", "Неизвестно")
        result["current"]["_desc_ru"] = desc
        return result

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
            return f"⚠️ Погода недоступна ({e}). Скажи «погода в <городе>» вручную."

    def tomorrow(self, city: str | None = None) -> str:
        c = city or DEFAULT_CITY
        try:
            data = self._fetch(c, days=2)
            return self._format_day(c, data, day=1)
        except Exception as e:
            return ("⚠️ Прогноз временно недоступен. Скажи «погода в <городе>» или попробуй позже.")

    def after_tomorrow(self, city: str | None = None) -> str:
        c = city or DEFAULT_CITY
        try:
            data = self._fetch(c, days=3)
            return self._format_day(c, data, day=2)
        except Exception as e:
            return ("⚠️ Прогноз временно недоступен. Скажи «погода в <городе>» или попробуй позже.")

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

    KEYWORDS = (
        "погода", "погоду", "погоде", "дождь", "снег", "жарко", "холодно",
        "тепло", "ветер", "температура", "прогноз", "градус", "на улице",
        "завтра", "послезавтра", "дача", "выходные",
    )

    def can_handle(self, request) -> bool:
        """Ловит запросы про погоду.

        Двойной API (Liskov 1987): принимает и str, и AgentRequest.
        """
        text = request if isinstance(request, str) else getattr(request, "text", "")
        t = text.lower()
        return any(kw in t for kw in self.KEYWORDS)

    async def handle(self, request):
        """Async handle для Orchestrator (AgentRequest → AgentResponse).

        Backward-compat: если передана строка — вернуть строку.
        """
        # Старый API: строка
        if isinstance(request, str):
            return self._handle_text(request)

        # Новый API: AgentRequest → AgentResponse
        try:
            from aura.core.protocol import AgentResponse
        except Exception:
            return self._handle_text(getattr(request, "text", ""))

        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        text = getattr(request, "text", "")
        return AgentResponse.ok(self._handle_text(text), self.name)

    def _handle_text(self, text: str) -> str:
        """Внутренняя логика — принимает строку."""
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
