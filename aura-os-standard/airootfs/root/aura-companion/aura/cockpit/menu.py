"""Menu — структура кабинета по зонам.

Верхний уровень — главный шлюз. Внутри зоны — свои действия.
Всё через цифры. Никаких команд.

Наука: Nielsen 1993 (recognition over recall),
       Campbell 1949 (зоны = акты Hero's Journey).
"""

from __future__ import annotations

from dataclasses import dataclass

from aura.game.state import StateStore
from aura.lore.story import StoryLog, get_briefing


@dataclass
class MenuAction:
    """Что выбрал капитан."""

    zone: str              # главная зона
    action: str | None = None  # действие внутри зоны
    arg: str | None = None


# ── Зоны верхнего уровня ───────────────────────────────
ZONES: list[tuple[str, str]] = [
    ("rest",     "🛏  Зона отдыха      (статус, брифинг, дневник)"),
    ("cockpit",  "🚀 Кабина пилота    (скан, квесты, Problem)"),
    ("arsenal",  "📦 Боезапас         (оружие, паттерны, апгрейд)"),
    ("journal",  "📋 Журнал           (маневры, поиск, экспорт)"),
    ("memory",   "🧠 Память           (заметки, RAG, файлы)"),
    ("comm",     "📡 Связь            (Дядя Р2, VK, календарь)"),
    ("settings", "⚙️  Настройки        (mute, volume, voice)"),
    ("pc",       "🖥  Управление ПК    (яркость, звук)"),
    ("oneshot",  "🩹 СПУСТИТЬ ВОЗДУХ  (починить всё одной кнопкой)"),
]


# ── Подменю по зонам ───────────────────────────────────
SUB_MENUS: dict[str, list[tuple[str, str]]] = {
    "rest": [
        ("status",   "HUD корабля"),
        ("form",     "🌐 Форма корабля (цифровой след)"),
        ("form_v",   "🌐 Форма — подробно"),
        ("brief",    "Брифинг"),
        ("diary",    "Дневник (последний день)"),
        ("remind",   "Напомнить через N минут"),
    ],
    "cockpit": [
        ("scan",     "🔭 Сканировать сектор"),
        ("quest",    "🚀 ВЫЛЕТ — зачистить"),
        ("problem",  "🎯 Разбор одной проблемы"),
    ],
    "arsenal": [
        ("weapons",  "Текущий арсенал"),
        ("patterns", "База паттернов"),
        ("upgrade",  "Апгрейд за XP"),
    ],
    "journal": [
        ("tail",     "Последние 10 записей"),
        ("search",   "Поиск по журналу"),
        ("export",   "Экспорт в файл"),
    ],
    "memory": [
        ("note",     "Записать заметку"),
        ("find",     "Найти в файлах"),
        ("read_story", "Прочитать STORY.md"),
        ("read_roadmap", "Прочитать ROADMAP"),
    ],
    "comm": [
        ("deepseek", "Спросить Дядю Р2"),
        ("vk",       "VK действия"),
        ("calendar", "Календарь (когда будет)"),
    ],
    "settings": [
        ("mute",     "Mute вкл/выкл"),
        ("volume",   "Громкость"),
        ("voice",    "Голос (проверка)"),
        ("deep",     "🔍 Глубокая проверка системы"),
    ],
    "pc": [
        ("panel",    "🖥  Панель управления ПК"),
    ],
    "oneshot": [
        ("run",      "🩹 Запустить ONE-SHOT"),
        ("dry",      "🔍 Dry-run (что будет сделано)"),
    ],
}


def parse_zone_choice(raw: str, count: int = len(ZONES)) -> str | None:
    """Разобрать выбор зоны: 1..N. 0 = выход, Enter = остаться."""
    raw = raw.strip()
    if raw in ("0", "q", "quit", "exit"):
        return None
    if raw == "":
        return None  # просто перерисовать меню
    if not raw.isdigit():
        return None
    idx = int(raw)
    if 1 <= idx <= count:
        return ZONES[idx - 1][0]
    return None


def parse_sub_choice(raw: str, zone: str) -> str | None:
    """Разобрать выбор внутри зоны."""
    raw = raw.strip()
    if raw in ("0", "q", ""):
        return None
    if not raw.isdigit():
        return None
    items = SUB_MENUS.get(zone, [])
    idx = int(raw)
    if 1 <= idx <= len(items):
        return items[idx - 1][0]
    return None


# ── Данные для рендера ─────────────────────────────────
def zone_menu_lines(zone: str) -> list[str]:
    items = SUB_MENUS.get(zone, [])
    return [f"  [{i}] {label}" for i, (_, label) in enumerate(items, 1)]


def build_status_lines() -> list[str]:
    store = StateStore()
    state = store.load()
    story = StoryLog()
    try:
        day = state.days_on_planet()
    except Exception:
        day = 1
    lines = [
        f"Сектор:  {state.sector}",
        f"Щиты:    {state.shields}%",
        f"Корпус:  {state.hull} узлов",
        f"XP:      {state.xp}",
        f"Ранг:    {state.rank} (уровень {state.level})",
        f"День:    {day}",
        f"Манёвры: {story.count_maneuvers()}",
    ]
    store.close()
    return lines


def build_journal_lines(n: int = 8) -> list[str]:
    story = StoryLog()
    tail = story.get_journal_tail(n)
    return tail.splitlines() if tail else ["(журнал пуст)"]


def build_brief_lines() -> list[str]:
    store = StateStore()
    state = store.load()
    story = StoryLog()
    line = get_briefing(state, story=story)
    store.close()
    return [line]


__all__ = [
    "SUB_MENUS",
    "ZONES",
    "MenuAction",
    "build_brief_lines",
    "build_journal_lines",
    "build_status_lines",
    "parse_sub_choice",
    "parse_zone_choice",
    "zone_menu_lines",
]
