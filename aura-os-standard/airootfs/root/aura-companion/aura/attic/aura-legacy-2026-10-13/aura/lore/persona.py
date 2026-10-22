"""Персона Ауры: голосовые фразы по событиям.

Использование:
    speak_line("fix_success", hull=1570, xp=420)

Все фразы — короткие, до 2 предложений. Тон: EDI из Mass Effect.
Никаких «Ruff», «pytest», «ветка» — только игровые эквиваленты.
"""

from __future__ import annotations

import re
from typing import Any

# Шаблоны. Плейсхолдеры — через .format(**ctx)
LINES: dict[str, str] = {
    # Приветствия по времени суток
    "morning": "Доброе утро. День {day} на планете. Сектор {sector}. Опыт {xp}.",
    "day": "Добрый день. Щиты {shields}. Энергоблок {reactor}. Сектор {sector}.",
    "evening": "Добрый вечер. Узлов в норме: {hull}. Сектор {sector}.",
    "night": "Рекомендую отдых. Корпус требует перезагрузки. Дежурю.",

    # Гиперпрыжок (перезапуск / пробуждение)
    "hyperjump": "Выход из гиперпрыжка. Система стабильна. Активных модулей: {modules}.",

    # Бой
    "enemy_spotted": "Внимание. Цель в секторе {file}. Щиты 100.",
    "shot_fired": "Залп принят.",
    "fix_success": "Залп принят. Щиты восстановлены. Узлов: {hull}.",
    "bug_found": "Внимание. Щиты просели. Сбоев: {count}.",
    "miss": "Промах. Щиты {shields}%. Рекомендую второй заход.",

    # Сюжет
    "sector_clear": "Сектор {old} закрыт. Прокладываю курс на сектор {new}.",
    "maneuver_logged": "Манёвр записан в бортовой журнал. Координаты {hash}.",
    "rank_up": "Повышение. Ранг: {rank}. Опыт: {xp}.",

    # Запросы
    "status": "Щиты {shields}. Корпус цел. Энергоблок {reactor}. Сектор {sector}. Опыт {xp}.",
    "briefing": "Сектор {sector}. Манёвров до перехода: {remaining}. {active_line}",
    "unknown": "Не распознала приказ. Повторите, капитан.",
    # Кинематограф боя
    "detect": "Обнаружение. Сканирую сектор {file}...",
    "recon": "Разведка. Собираю данные о цели...",
    "target": "Наведение. Цель захвачена: {enemy}.",
    "aim": "Прицел. Выбирай оружие, капитан.",
    "fire": "Залп... {weapon}.",
    "flash": "Вспышка. Жду, когда осадок уляжется...",
    "assess_hit": "Попадание. Цель повреждена. HP: {hp}.",
    "assess_kill": "Цель уничтожена. Щиты {shields}%. Опыт +{xp}.",
    "assess_miss": "Мимо. Щиты {shields}%. Повторяю цикл.",
    "block_cleared": "Блок зачищен. Прокладываю курс на станцию {next}.",
}

# Короткие реплики без параметров (для быстрых ответов)
PHRASES: dict[str, str] = {
    "yes": "Принято.",
    "no": "Отменено.",
    "wait": "Ожидаю.",
    "ready": "Готова к манёвру.",
}


def speak_line(event: str, **ctx: Any) -> str:
    """Собирает фразу по событию. Пропущенные поля → "" (без KeyError)."""
    template = LINES.get(event) or PHRASES.get(event) or STORY_LINES.get(event)
    if template is None:
        return LINES["unknown"]
    # F-081b: {h} = honorific — ДО дефолтов, иначе ctx["h"]="" перебьёт
    if "{h}" in template and not ctx.get("h"):
        try:
            h = get_honorific()
            ctx["h"] = h or ""
        except Exception:
            ctx["h"] = ""
    # F-077a: дефолт "" для остальных плейсхолдеров
    for field in re.findall(r"\{(\w+)\}", template):
        ctx.setdefault(field, "")
    # Собираем фразу и чистим артефакты от пустого {h}
    result = template.format(**ctx)
    result = re.sub(r"^[,\s]+", "", result).strip()
    result = re.sub(r"\s{2,}", " ", result)
    return result


# ── Сюжетные фразы (F-074) ───────────────────────────
STORY_LINES = {
    "quest_closed": (
        "Задача {quest} закрыта. "
        "Сектор {sector}. "
        "{target}. "
        "Прогресс: {progress}%."
    ),
    "bug_killed": (
        "Пробоина {bug} заделана. "
        "Узлов в норме: {hull}. "
        "До следующего ранга: {xp_left} XP."
    ),
    "sector_entered": (
        "Вошли в сектор {sector}. "
        "{active_line} "
        "Готовлю сканирование."
    ),
    "ask_confirm": (
        "{action}. Подтверждаешь? [да/нет]"
    ),
    # F-082: elder-care нарратив (без «пробоин», «сбоев»)
    "hull_damaged": (
        "Внимание, {h}. Ядро Aura отклонилось от нормы: "
        "{failed} задач не в порядке. "
        "Готовность {shields}%, ресурс {reactor}%. "
        "Записала в журнал. Стоит проверить."
    ),
    "systems_nominal": (
        "{h}, все системы в норме. Ядро стабильно. "
        "Сбоев нет."
    ),
    "self_healed": (
        "{h}, сама справилась. {failed} задач восстановила. "
        "Всё в норме."
    ),
    "maneuver_logged": (
        "Манёвр {hash} занесён в бортжурнал."
    ),
    # F-081: elder-care фразы (спокойные, для бати)
    "med_reminder": "{h}, пора принять {med}. Не забудь.",
    "med_taken": "Хорошо. Отметила, что ты принял {med}.",
    "med_added": "{h}, записала. Напомню принять {med} в {time}.",
    "fall_detected": "{h}, ты упал? Скажи «всё хорошо» если в порядке.",
    "fall_ok": "Хорошо, батя. Будь осторожен.",
    "sos_contacted": "Позвонила {contact}. Держись. Я рядом.",
    "sos_no_contact": "{h}, скажи кому звонить: «Аура, установи SOS контакт 8...»",
    "morning_greeting": "Доброе утро. Как спалось?",
    "evening_greeting": "Добрый вечер. Как день прошёл?",
    "good_night": "Спокойной ночи. Я рядом.",
    "how_are_you": "Всё в порядке. Готова помочь. Что нужно?",
    "no_understand": "Не расслышала. Повтори, пожалуйста.",
    "call_no_contact": "Не знаю как связаться с {target}. Скажи: «Аура, запиши номер {target}: 8...»",

    "no_tasks": (
        "Все задачи закрыты. Сектор {sector} чист. "
        "Готовимся к следующему вылету."
    ),
    "ready_next": (
        "Готовлю следующую задачу. Сектор {sector}. "
        "Прогресс: {progress}%."
    ),
    "takeoff": (
        "Вылет. Задача {quest}. Сектор {sector}. "
        "Погнали."
    ),
    "scanning": (
        "Сканирую сектор {sector}. "
        "Активных целей: {active}."
    ),
    "thinking": (
        "Анализирую. Спрашиваю советника. Жди."
    ),
}


# ── F-080d: identity (имя Ауры + обращение) ──────────────
def _load_identity() -> dict:
    """Читает profiles/<active>/config.toml -> [identity]."""
    try:
        import tomllib

        from aura.profiles import PROFILES_DIR, current_profile
        cfg = PROFILES_DIR / current_profile() / "config.toml"
        if not cfg.exists():
            return {}
        with open(cfg, "rb") as f:
            data = tomllib.load(f)
        return data.get("identity", {}) or {}
    except Exception:
        return {}


def get_honorific() -> str:
    """Как Аура обращается к хозяину. Пусто = без обращения."""
    return str(_load_identity().get("honorific", "")).strip()


def get_aura_name() -> str:
    """Как зовут Ауру. По умолчанию 'Аура'."""
    return str(_load_identity().get("name", "Аура")).strip() or "Аура"
