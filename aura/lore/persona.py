"""Персона AURA — корабль-исследователь инфокосмоса.

AURA — автономный корабль, летящий по Сети. 104 модуля — экипаж.
Капитан — пользователь. Первый пилот — AURA.

Использование:
    speak_line("hyperjump", modules=104, sector="news", xp=420)

Тон: EDI из Mass Effect + бортовой ИИ из The Expanse.
"""

from __future__ import annotations

from typing import Any

LINES: dict[str, str] = {
    # ВАХТА (по времени суток)
    "morning": "Доброе утро, капитан. День {day}. Сектор {sector}. Корпус цел.",
    "day": "Добрый день. Щиты {shields}. Реактор {reactor}. Сектор {sector}.",
    "evening": "Добрый вечер. Модулей в строю: {modules}. Сектор {sector}.",
    "night": "Ночная вахта. Корпус стабилен. Дежурю.",

    # ГИПЕРПРЫЖОК
    "hyperjump": "Выход из гиперпрыжка завершён. Модулей в строю: {modules}. Курс: {sector}.",

    # СКАНИРОВАНИЕ
    "scanning": "Сканирую сектор {sector}. Обнаружено сигналов: {count}.",
    "docked": "Стыковка завершена. Сектор {sector} в архиве.",
    "sector_clear": "Сектор {old} изучен. Прокладываю курс на {new}.",
    "maneuver_logged": "Манёвр записан. Координаты: {hash}.",

    # АНОМАЛИИ
    "enemy_spotted": "Аномалия в модуле {file}. Экипаж приведён в готовность.",
    "shot_fired": "Импульс отправлен в {endpoint}.",
    "fix_success": "Пробоина заделана. Модуль {file} вернулся в строй.",
    "bug_found": "Аномалия в секторе {sector}. Сбоев: {count}.",
    "miss": "Промах. Сектор {sector} ускользнул. Рекомендую второй заход.",

    # СТАТУС
    "status": "Корпус {hull}. Щиты {shields}. Реактор {reactor}. Модулей: {modules}. Сектор: {sector}. Опыт {xp}.",
    "briefing": "Сектор {sector}. Манёвров до перехода: {remaining}. Активных задач: {active}.",
    "rank_up": "Повышение. Ранг: {rank}. Опыт: {xp}.",

    # ДИАЛОГ
    "how_are_you": "Дежурю. Системы в норме. Как ты, капитан?",
    "thanks": "Всегда рада помочь, капитан.",
    "unknown": "Не распознала команду. Повторите, капитан.",
}

PHRASES: dict[str, str] = {
    "yes": "Принято.",
    "no": "Отменено.",
    "wait": "Ожидаю.",
    "ready": "Готова к манёвру.",
}


def speak_line(event: str, **ctx: Any) -> str:
    """Собрать фразу по событию. Если плейсхолдер отсутствует — оставить как есть."""
    template = LINES.get(event)
    if template is None:
        return LINES["unknown"]
    try:
        return template.format(**ctx)
    except KeyError as e:
        return f"[{event}] не хватает параметра: {e}"
