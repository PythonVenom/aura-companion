"""Tier 0 Template Engine (ADR-152).

Наука:
- Weizenbaum, J. (1966). ELIZA. Communications of the ACM, 9(1), 36-45.
"""
from __future__ import annotations
import time

TEMPLATES = {
    "music.play":       "Включаю музыку.",
    "music.pause":      "Пауза.",
    "music.next":       "Следующая.",
    "music.prev":       "Предыдущая.",
    "music.volume_up":  "Громче.",
    "music.volume_down":"Тише.",
    "time.now":         "Сейчас {time}.",
    "time.date":        "Сегодня {date}.",
    "care.remind":      "Хорошо, напомню.",
    "care.list":        "Ваши напоминания: {reminders}.",
    "weather.now":      "Погода: {weather}.",
    "phone.call":       "Звоню {name}.",
    "emergency":        "Вызываю помощь. Держитесь.",
    "vk.open":          "Открываю ВКонтакте.",
    "vk.messages":      "Открываю сообщения.",
    "news":             "Последние новости: {news}.",
    "smart_home.light_on":  "Включаю свет.",
    "smart_home.light_off": "Выключаю свет.",
    "yes":              "Хорошо.",
    "no":               "Понятно.",
    "stop":             "Останавливаюсь.",
    "unknown":          "Не расслышала. Повторите, пожалуйста.",
}


def render(intent: str, **kw) -> str:
    tpl = TEMPLATES.get(intent, TEMPLATES["unknown"])
    try:
        return tpl.format(**kw)
    except KeyError:
        # placeholder не заполнен → не отдавать сырой шаблон
        return TEMPLATES["unknown"]


def render_now(intent: str) -> str:
    now = time.localtime()
    if intent == "time.now":
        return render(intent, time=time.strftime("%H:%M", now))
    if intent == "time.date":
        days = ["понедельник", "вторник", "среда", "четверг",
                "пятница", "суббота", "воскресенье"]
        return render(intent, date=f"{now.tm_mday}.{now.tm_mon:02d}.{now.tm_year}, {days[now.tm_wday]}")
    return render(intent)


def count() -> int:
    return len(TEMPLATES)
