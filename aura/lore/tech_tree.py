"""F-093: Дерево технологий (X3 tech-tree).

Агенты — технологии. XP — топливо. Открытие — прогресс.

Наука:
- X3: чертёж → станция → ветка
- Brooks 1975: данные отдельно, рендер отдельно
- Ries 2011: MVP сначала (визуализация + unlock)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TechNode:
    """Один узел дерева."""

    key: str                       # имя агента (matches registry)
    tier: int                      # 1 базовый, 2 продвинутый, 3 редкий
    xp_cost: int                   # сколько стоит открыть (0 = открыт)
    description: str
    requires: tuple[str, ...] = () # что должно быть открыто


# Только elder-care агенты (real agents из registry)
TECH_TREE: dict[str, TechNode] = {
    # ── Tier 1: базовые (всегда открыты) ───────────────
    "time":         TechNode("time", 1, 0, "Время и дата"),
    "greeting":     TechNode("greeting", 1, 0, "Приветствие"),
    "calendar":     TechNode("calendar", 1, 0, "Календарь событий"),
    "meds":         TechNode("meds", 1, 0, "Напоминания о лекарствах"),
    "fall":         TechNode("fall", 1, 0, "Детектор падения"),
    "call":         TechNode("call", 1, 0, "Звонки родным"),

    # ── Tier 2: продвинутые (за XP) ─────────────────────
    "sos":          TechNode("sos", 2, 500, "SOS — экстренный контакт",
                             requires=("fall", "call")),
    "weather":      TechNode("weather", 2, 300, "Погода",
                             requires=("knowledge",)),
    "fin_elder":    TechNode("fin_elder", 2, 800, "Финансы пожилых",
                             requires=("meds", "calendar")),
    "homeassistant": TechNode("homeassistant", 2, 1200, "Умный дом",
                              requires=("audio_router",)),
    "sensors":      TechNode("sensors", 2, 600, "Датчики",
                             requires=("homeassistant",)),

    # ── Tier 3: редкие ──────────────────────────────────
    "telegram":     TechNode("telegram", 3, 1500, "Telegram-бот",
                             requires=("messenger", "sms")),
    "vk_music":     TechNode("vk_music", 3, 2000, "VK музыка",
                             requires=("media_search", "audio_router")),
    "advisors":     TechNode("advisors", 3, 3000, "Советники (экипаж)",
                             requires=("rag_memory", "journal")),
}


def _get_unlocked(state) -> set[str]:
    """Какие уже открыты. Tier-1 (xp_cost=0) — всегда."""
    unlocked = {k for k, n in TECH_TREE.items() if n.xp_cost == 0}
    try:
        extra = getattr(state, "unlocked_tech", None)
        if isinstance(extra, (list, tuple, set)):
            unlocked.update(extra)
    except Exception:
        pass
    return unlocked


def can_unlock(key: str, state) -> tuple[bool, str]:
    """(можно?, причина)."""
    node = TECH_TREE.get(key)
    if node is None:
        return False, "неизвестно"
    unlocked = _get_unlocked(state)
    if key in unlocked:
        return False, "уже открыто"
    if node.xp_cost > getattr(state, "xp", 0):
        return False, f"нужно {node.xp_cost} XP"
    missing = [r for r in node.requires if r not in unlocked]
    if missing:
        return False, f"нужно: {', '.join(missing)}"
    return True, "ok"


def unlock(key: str, state) -> tuple[bool, str]:
    """Открыть узел. Списывает XP. Возвращает (успех, сообщение)."""
    ok, reason = can_unlock(key, state)
    if not ok:
        return False, reason
    node = TECH_TREE[key]
    if hasattr(state, "xp"):
        state.xp = max(0, state.xp - node.xp_cost)
    if hasattr(state, "unlocked_tech"):
        existing = list(state.unlocked_tech or [])
        if key not in existing:
            existing.append(key)
        state.unlocked_tech = existing
    return True, f"открыто: {node.description}"


def render_tree(state) -> str:
    """ASCII-дерево агентов."""
    unlocked = _get_unlocked(state)
    lines = [f"🎯 ДЕРЕВО ТЕХНОЛОГИЙ · XP: {getattr(state, 'xp', 0)}", ""]
    for tier in (1, 2, 3):
        label = {1: "Базовые", 2: "Продвинутые", 3: "Редкие"}[tier]
        nodes = [(k, n) for k, n in TECH_TREE.items() if n.tier == tier]
        if not nodes:
            continue
        lines.append(f"═══ Tier {tier} · {label} ═══")
        for key, node in nodes:
            mark = "✓" if key in unlocked else "🔒"
            cost = f"{node.xp_cost} XP" if node.xp_cost else "открыто"
            req = f" ← {', '.join(node.requires)}" if node.requires else ""
            lines.append(f"  [{mark}] {key:16} {cost:12} · {node.description}{req}")
        lines.append("")
    return "\n".join(lines)
