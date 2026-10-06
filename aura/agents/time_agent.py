"""TimeAgent — таймер, будильник."""
from __future__ import annotations
import json
import re
import time
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent

TIMERS_PATH = Path(str(Path.home() / ".cache/aura/aura_timers.json"))

# Bug E: ASR слышит "тридцать" вместо "30"
NUM_WORDS = {
    "один": 1, "два": 2, "три": 3, "четыре": 4, "пять": 5,
    "шесть": 6, "семь": 7, "восемь": 8, "девять": 9, "десять": 10,
    "пятнадцать": 15, "двадцать": 20, "тридцать": 30,
    "сорок": 40, "пятьдесят": 50,
}


def _parse_int(text: str):
    """Вернуть (число, остаток) или None."""
    # Сначала цифры
    m = __import__("re").search(r"(\d+)", text)
    if m:
        return int(m.group(1))
    # Потом слова
    for w in sorted(NUM_WORDS.keys(), key=len, reverse=True):
        if w in text.lower():
            return NUM_WORDS[w]
    return None


def _load():
    if not TIMERS_PATH.exists():
        return []
    try:
        return json.loads(TIMERS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(items):
    try:
        TIMERS_PATH.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        # F-006: не глотать (раздел 17 промта)
        import logging
        logging.getLogger('aura.time_agent').debug(
            'time_agent error: %s', e)


def add_timer(seconds, label=""):
    t = {"id": int(time.time() * 1000), "type": "timer",
         "fire_at": time.time() + seconds, "label": label or f"{seconds} сек"}
    items = _load(); items.append(t); _save(items); return t


def add_alarm(hour, minute, label=""):
    now = time.localtime()
    target = time.mktime((now.tm_year, now.tm_mon, now.tm_mday,
                          hour, minute, 0, 0, 0, -1))
    if target <= time.time():
        target += 86400
    a = {"id": int(time.time() * 1000), "type": "alarm",
         "fire_at": target, "label": label or f"{hour:02d}:{minute:02d}"}
    items = _load(); items.append(a); _save(items); return a


def list_pending():
    now = time.time()
    items = [x for x in _load() if x.get("fire_at", 0) > now]
    _save(items); return items


def get_fired():
    now = time.time()
    items = _load()
    fired = [x for x in items if x.get("fire_at", 0) <= now]
    pending = [x for x in items if x.get("fire_at", 0) > now]
    _save(pending); return fired


class AgentTimeAgent(BaseAgent):
    name = "time_agent"
    MODULE_ALWAYS = True
    KEYWORDS = ("таймер", "будильник", "разбуди в", "напомни через")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        import re as _re
        m = _re.search(r"(\d+)\s*(минут|мин|сек|секунд|час)", text)
        if not m and ("таймер" in text or "напомни через" in text):
            n_val = _parse_int(text)
            unit = "секунд" if "секунд" in text or "сек" in text else ("минут" if "минут" in text or "мин" in text else "час")
            if n_val:
                m = type("M", (), {"group": lambda self, i: str(n_val) if i == 1 else unit})()
        if m and ("таймер" in text or "напомни через" in text):
            n = int(m.group(1)); unit = m.group(2)
            if "час" in unit:
                sec = n * 3600
            elif unit.startswith("мин"):
                sec = n * 60
            else:
                sec = n
            add_timer(sec, f"{n} {unit}")
            return AgentResponse.ok(f"⏱ Таймер на {n} {unit}", self.name)

        m2 = re.search(r"в\s*(\d{1,2})[:. ](\d{2})", text)
        if m2 and ("будильник" in text or "разбуди" in text):
            h, mi = int(m2.group(1)), int(m2.group(2))
            add_alarm(h, mi, f"{h:02d}:{mi:02d}")
            return AgentResponse.ok(f"⏰ Будильник на {h:02d}:{mi:02d}", self.name)

        if "какие" in text or "покажи" in text:
            items = list_pending()
            if not items:
                return AgentResponse.ok("⏱ Нет активных", self.name)
            now = time.time()
            parts = [f"{it['label']} ({int(it['fire_at']-now)}с)" for it in items]
            return AgentResponse.ok("⏱ " + ", ".join(parts), self.name)

        return AgentResponse.not_handled(self.name)
