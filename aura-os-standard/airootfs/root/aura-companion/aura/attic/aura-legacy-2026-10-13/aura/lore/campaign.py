"""Карта секторов — главы кампании Aura.

X3: сектор → система → станция
Aura: сектор → модуль → агент → задача

Закрыт сектор = все задачи done.
Прыжок вперёд разрешён при >=80% закрытых задач предыдущего.
"""
from __future__ import annotations

SECTORS: dict[str, dict] = {
    "STABILIZE": {
        "chapter": 0,
        "title": "Стабилизация",
        "desc": "Батя. Elder-care MVP. Watchdog, микрофон, RAG.",
        "prev": None,
        "next": "FORMALIZE",
        "tasks": [
            {"id": "F-074", "title": "Сюжетный дебрифинг",     "done": True},
            {"id": "F-074b","title": "persona.py в репо",       "done": True},
            {"id": "F-074c","title": "Singleton голоса",        "done": True},
            {"id": "F-075", "title": "Карта секторов + jump",   "done": True},
            {"id": "F-076b","title": "Восстановление щитов",    "done": True},
            {"id": "F-077a","title": "briefing без KeyError",   "done": True},
            {"id": "F-080", "title": "install_batya.sh v2",     "done": False},
            {"id": "F-086", "title": "use_llm из profile",      "done": True},
        ],
    },
    "FORMALIZE": {
        "chapter": 1,
        "title": "Учения",
        "desc": "Формализуем elder-care. Тесты, доки, конституция.",
        "prev": "STABILIZE",
        "next": "ORACLE",
        "tasks": [
            {"id": "F-078", "title": "hardware_detect + pytest -n", "done": True},
            {"id": "F-079", "title": "per-profile modules",         "done": True},
            {"id": "F-080b","title": "Meds/Fall/Call до Calendar",  "done": True},
            {"id": "F-080d","title": "identity per-profile",        "done": True},
            {"id": "F-080f","title": "Calendar до Call",            "done": True},
            {"id": "F-081", "title": "speak_line → STORY_LINES",    "done": True},
            {"id": "F-082", "title": "elder-care нарратив",         "done": True},
            {"id": "F-084", "title": "AgentWeather",                "done": True},
            {"id": "F-085", "title": "AgentGreeting",               "done": True},
        ],
    },
    "ORACLE": {
        "chapter": 2,
        "title": "Оракул",
        "desc": "RAG, знания, контекст. Аура учится помнить.",
        "prev": "FORMALIZE",
        "next": "HARDEN",
        "tasks": [
            {"id": "F-073", "title": "Lazy ChromaDB",         "done": True},
            {"id": "F-073b","title": "Bootstrap 0.14s",       "done": True},
            {"id": "RAG-1", "title": "2533 диалога",          "done": True},
            {"id": "RAG-2", "title": "embeddings[0] fix",     "done": True},
            {"id": "RAG-3", "title": "Контекст в ответе",     "done": False},
            {"id": "RAG-4", "title": "RAG в бою (враги)",     "done": False},
        ],
    },
    "HARDEN": {
        "chapter": 3,
        "title": "Крепость",
        "desc": "SQLCipher, безопасность, отказоустойчивость.",
        "prev": "ORACLE",
        "next": "EXPAND",
        "tasks": [
            {"id": "SEC-1", "title": "SQLCipher AES-256",     "done": True},
            {"id": "SEC-2", "title": "Capability system",      "done": True},
            {"id": "SEC-3", "title": "Oneshot автофикс",       "done": True},
            {"id": "SEC-4", "title": "CI (GitHub Actions)",    "done": False},
            {"id": "SEC-5", "title": "make doctor",            "done": False},
        ],
    },
    "EXPAND": {
        "chapter": 4,
        "title": "Экспансия",
        "desc": "Платформы, плагины, другие Aura.",
        "prev": "HARDEN",
        "next": "FRONTIER",
        "tasks": [
            {"id": "EXP-1", "title": "11 платформ",           "done": True},
            {"id": "EXP-2", "title": "Astra Linux SE",        "done": False},
            {"id": "EXP-3", "title": "Android адаптер",       "done": False},
            {"id": "EXP-4", "title": "Plugin manager",        "done": True},
        ],
    },
    "FRONTIER": {
        "chapter": 5,
        "title": "Фронтир",
        "desc": "Elbrus e2k, Aura OS, LFS. Горизонт — не бой.",
        "prev": "EXPAND",
        "next": None,
        # F-101c: attackable=False — эти задачи не решаются боем,
        # только реальной работой (LLama PR, LFS-сборка).
        "attackable": False,
        "tasks": [
            {"id": "F-162", "title": "Aura OS (LFS + e2k)",   "done": False},
            {"id": "F-038", "title": "Elbrus e2k (llama.cpp)", "done": False},
            {"id": "F-161", "title": "Aura ISO дистрибутив",  "done": False},
        ],
    },
}


def get_current() -> str:
    """Текущий сектор из state. Fallback — STABILIZE."""
    try:
        from aura.game.state import StateStore
        s = StateStore().load()
        return getattr(s, "sector", "STABILIZE") or "STABILIZE"
    except Exception:
        return "STABILIZE"


def get_sector(name: str) -> dict | None:
    return SECTORS.get(name.upper())


def get_next(name: str) -> str | None:
    sec = get_sector(name)
    return sec["next"] if sec else None


def get_prev(name: str) -> str | None:
    sec = get_sector(name)
    return sec["prev"] if sec else None


def sector_progress(name: str) -> dict:
    """Прогресс сектора: done/total/pct/is_closed.

    F-101: задачи, закрытые в state.quests_done, перекрывают статический
    флаг done=True в campaign.py. Так игрок может проходить задачи боем.
    """
    sec = get_sector(name)
    if not sec:
        return {"done": 0, "total": 0, "pct": 0, "is_closed": False}
    tasks = sec.get("tasks", [])
    total = len(tasks)
    if total == 0:
        return {"done": 0, "total": 0, "pct": 0, "is_closed": False}

    # Читаем quests_done из state
    try:
        from aura.game.state import StateStore
        s = StateStore()
        st = s.load()
        s.close()
        done_ids = set(getattr(st, "quests_done", []) or [])
    except Exception:
        done_ids = set()

    # Задача закрыта, если (static done) ИЛИ (в quests_done)
    done = 0
    for t in tasks:
        if t.get("done") or t.get("id") in done_ids:
            done += 1

    pct = int(done / total * 100)
    return {
        "done": done,
        "total": total,
        "pct": pct,
        "is_closed": pct >= 80,
    }


def open_tasks(name: str) -> list[dict]:
    """Незакрытые задачи сектора (для боя)."""
    sec = get_sector(name)
    if not sec:
        return []
    tasks = sec.get("tasks", [])

    try:
        from aura.game.state import StateStore
        s = StateStore()
        st = s.load()
        s.close()
        done_ids = set(getattr(st, "quests_done", []) or [])
    except Exception:
        done_ids = set()

    return [
        t for t in tasks
        if not t.get("done") and t.get("id") not in done_ids
    ]


def all_sectors_progress() -> dict[str, dict]:
    return {name: sector_progress(name) for name in SECTORS}


def can_jump(from_name: str, to_name: str) -> tuple[bool, str]:
    """Разрешён ли прыжок.

    Правило: если from закрыт >=80% → любой to разрешён.
    Иначе → только откат (to в visited или предок).
    """
    sec_from = get_sector(from_name)
    sec_to = get_sector(to_name)
    if not sec_from or not sec_to:
        return False, "Сектор не найден"

    prog = sector_progress(from_name)
    if prog["is_closed"]:
        return True, f"✅ {from_name} закрыт ({prog['pct']}%)"

    # Разрешаем откат к prev
    if sec_to.get("chapter", 0) < sec_from.get("chapter", 0):
        return True, f"↩ Откат к {to_name}"

    return False, (
        f"⚠️ {from_name} закрыт на {prog['pct']}%. "
        f"Нужно >=80% для прыжка в {to_name}."
    )


def render_map() -> str:
    """ASCII-карта секторов с прогрессом."""
    current = get_current()
    lines = ["🛸 КАРТА СЕКТОРОВ", ""]
    for name, meta in SECTORS.items():
        prog = sector_progress(name)
        if name == current:
            mark = "🎯"
        elif prog["is_closed"]:
            mark = "✅"
        elif prog["done"] > 0:
            mark = "🟡"
        else:
            mark = "🔒"
        lines.append(
            f"  [{mark}] {name:10} · гл.{meta['chapter']} · {meta['title']:12} "
            f"· {prog['done']}/{prog['total']} ({prog['pct']}%)"
        )
        lines.append(f"        {meta['desc']}")
    return "\n".join(lines)


__all__ = [
    "SECTORS",
    "all_sectors_progress",
    "can_jump",
    "get_current",
    "get_next",
    "get_prev",
    "get_sector",
    "render_map",
    "sector_progress",
]
