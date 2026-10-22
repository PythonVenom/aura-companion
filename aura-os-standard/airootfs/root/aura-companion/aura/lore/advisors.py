"""F-092: Советники — экипаж Aura (Mass Effect squad).

3 персонажа. Каждый со своим голосом и ролью:

  Инженер    — советы по коду, багам, архитектуре
  Навигатор  — советы по секторам, куда лететь
  Тактик     — советы по бою, оружию

Наука: Brooks 1975 (тонкие обёртки), Campbell 1949 (архетипы),
       Mass Effect (squadmates).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Advisor:
    """Один советник."""

    key: str              # машинное имя
    name: str             # отображаемое имя
    role: str             # роль
    voice: str            # тембр голоса (для piper)
    color: str            # цвет в TUI
    emoji: str            # иконка
    motto: str            # девиз при первом появлении


ADVISORS: dict[str, Advisor] = {
    "engineer": Advisor(
        key="engineer",
        name="Тара",
        role="Инженер",
        voice="ru_RU-irina-medium",
        color="#00ff88",
        emoji="🔧",
        motto="Хочешь — починим. Хочешь — переделаем.",
    ),
    "navigator": Advisor(
        key="navigator",
        name="Кай",
        role="Навигатор",
        voice="ru_RU-dmitri-medium",
        color="#00ffff",
        emoji="🧭",
        motto="Курс — прежде всего.",
    ),
    "tactician": Advisor(
        key="tactician",
        name="Рэй",
        role="Тактик",
        voice="ru_RU-irina-medium",
        color="#ff6666",
        emoji="⚔",
        motto="Лучший бой — тот, что выигран заранее.",
    ),
}


def get_advisor(key: str) -> Advisor | None:
    return ADVISORS.get(key)


def list_advisors() -> list[Advisor]:
    return list(ADVISORS.values())


def render_roster() -> str:
    """ASCII-список экипажа."""
    lines = ["👥  ЭКИПАЖ AURA", ""]
    for a in ADVISORS.values():
        lines.append(f"  {a.emoji}  {a.role:12} · {a.name:8} · {a.motto}")
    return "\n".join(lines)

# ── F-092b: диалоги советников ───────────────────────────
ADVISOR_LINES: dict[str, dict[str, list[str]]] = {
    "engineer": {
        "sector_clean": [
            "Сектор чист, капитан. Модули в норме.",
            "Корпус цел. Ни одной пробоины.",
            "Проверка завершена. Всё стабильно.",
        ],
        "sector_dirty": [
            "Пробоин: {n}. Рекомендую залп.",
            "Нашла {n} сбоев. Приступаем?",
            "{n} узлов не в порядке. Начинаю диагностику.",
        ],
        "battle_start": [
            "Боевой пост готов. Держи ровно.",
            "Сканирую цель. По моей команде — залп.",
        ],
        "battle_win": [
            "Чисто сработано. Корпус в норме.",
            "Пробоина заделана. Молодец.",
        ],
        "battle_lose": [
            "Щиты утекли. Возвращаемся в док?",
            "Плохо. Рекомендую отступить.",
        ],
    },
    "navigator": {
        "sector_clean": [
            "Курс свободен. До следующего сектора — прыжок.",
            "Ни препятствий. Готов к гиперпрыжку.",
        ],
        "sector_dirty": [
            "На пути {n} объектов. Обходим?",
            "Сканирую. Рекомендую аккуратный подход.",
        ],
        "jump_ready": [
            "Следующий сектор: {next}. Прыгаем?",
            "Готов к прыжку в {next}. Подтверди.",
        ],
        "jump_done": [
            "Прыжок завершён. Сектор: {sector}.",
            "Прибыли. {sector}. Разворачиваю сканирование.",
        ],
    },
    "tactician": {
        "sector_clean": [
            "Тишина — не значит покой. Будь наготове.",
            "Сектор чист. Но я бы не расслаблялся.",
        ],
        "sector_dirty": [
            "Целей: {n}. Точный залп — шанс 85%.",
            "{n} противников. Ракета — риск, но урон выше.",
        ],
        "battle_start": [
            "Оцениваю. Точный залп — самый надёжный.",
            "Не торопись. Сначала цель, потом огонь.",
        ],
        "battle_win": [
            "Чисто. Так и надо.",
            "Хороший выстрел. Держим темп.",
        ],
        "battle_lose": [
            "Плохо. Отступаем и перегруппируемся.",
            "Не наш день. Возвращаемся.",
        ],
    },
}


def advisor_speak(key: str, context: str, **ctx) -> str | None:
    """Собрать фразу советника по контексту.

    Args:
        key: 'engineer' | 'navigator' | 'tactician'
        context: 'sector_clean' | 'sector_dirty' | 'battle_start' | ...
        **ctx: параметры для подстановки (n, next, sector, ...)

    Returns:
        Строка фразы или None.
    """
    import random
    adv_lines = ADVISOR_LINES.get(key, {})
    lines = adv_lines.get(context, [])
    if not lines:
        return None
    template = random.choice(lines)
    try:
        return template.format(**ctx)
    except KeyError:
        return template


def all_voices() -> list[str]:
    """Список голосов piper для советников."""
    return list({a.voice for a in ADVISORS.values()})
