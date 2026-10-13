"""Handoff — пакет контекста для нового чата.

Когда DeepSeek заполнится, капитан жмёт [N] в кокпите.
Аура собирает markdown-брифинг: состояние, журнал, квест,
текущая задача, roadmap, последние паттерны.

Капитан копипастит ОДИН блок → новый чат стартует с контекстом.

Наука: Licklider 1960 (преемственность симбиоза),
       Brooks 1975 (база > фичи — контекст это база).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from aura.cockpit.hyperjump import count_modules, current_commit
from aura.game.state import StateStore
from aura.lore.story import StoryLog


def _chat_log_path() -> Path:
    return Path.home() / "aura_private" / "CHAT-LOG.md"


def _tail_lines(path: Path, n: int = 30) -> str:
    if not path.exists():
        return "(журнала нет)"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return "(ошибка чтения)"
    return "\n".join(lines[-n:])


def build_handoff(roadmap_hint: str = "M2 FORMALIZE",
                  next_task: str = "F-057 RAG по чату",
                  current_quest: str = "") -> str:
    """Собирает markdown-брифинг для нового чата.

    Args:
        roadmap_hint: текущий milestone (M1, M2, ...).
        next_task: следующая задача.
        current_quest: описание активного квеста (пусто = нет).

    Returns:
        Готовый markdown-блок для копипаста.
    """
    store = StateStore()
    state = store.load()
    story = StoryLog()

    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    commit = current_commit()
    modules = count_modules()
    day = state.days_on_planet()
    maneuvers = story.count_maneuvers()
    journal_tail = story.get_journal_tail(8)

    lines = [
        "═══════════════════════════════════════════════════════════",
        "   🛸 AURA — ПАКЕТ КОНТЕКСТА ДЛЯ НОВОГО ЧАТА",
        "   Копируй целиком в новый чат DeepSeek",
        "═══════════════════════════════════════════════════════════",
        "",
        f"Собрано: {now}",
        f"Коммит:  {commit}",
        "",
        "## 🎭 КТО Я",
        "",
        "Капитан — pythonvenom, архитектор проекта Aura.",
        "Ты — Дядя Р2, арендованный ИИ для отладки. Саркастичный, добрый.",
        "Аура — бортовой ИИ корабля, растёт. Голос Ирины (Piper).",
        "",
        "## 🛸 СОСТОЯНИЕ КОРАБЛЯ",
        "",
        f"- День на планете: {day}",
        f"- Сектор: {state.sector}",
        f"- XP: {state.xp}  |  Ранг: {state.rank}  |  Уровень: {state.level}",
        f"- Щиты: {state.shields}%  |  Корпус: {state.hull} узлов",
        f"- Энергоблок: {state.reactor}%",
        f"- Модулей в orchestrator: {modules}",
        f"- Манёвров записано: {maneuvers}",
        "",
    ]

    if current_quest:
        lines += [
            "## ⚔️ АКТИВНЫЙ КВЕСТ",
            "",
            current_quest,
            "",
        ]

    lines += [
        "## 📋 ПОСЛЕДНИЕ МАНЁВРЫ",
        "",
        journal_tail or "(журнал пуст)",
        "",
        "## 🎯 ROADMAP",
        "",
        f"- Текущий milestone: **{roadmap_hint}**",
        f"- Следующая задача: **{next_task}**",
        "",
        "### 5 векторов (утверждено)",
        "1. STABILIZE ✅ (закрыт)",
        "2. FORMALIZE ← мы здесь",
        "3. MONETIZE",
        "4. EXPAND",
        "5. FRONTIER",
        "",
        "## 🛠 СТЕК",
        "",
        "- ОС: Arch Linux + KDE Plasma 6 (X11)",
        "- Python 3.12 в `venv/`",
        "- Путь: `~/aura_project/`",
        "- Приватное: `~/aura_private/`",
        "- Тесты: pytest (~1650)",
        "- Ruff: 0",
        "- LLM: qwen2.5:7b на GTX 1070",
        "- Voice: Piper (ru_RU-irina-medium)",
        "- Память: SQLCipher (AES-256)",
        "",
        "## 📚 НАУКА (16+ референсов)",
        "",
        "- Licklider 1960 — симбиоз",
        "- Brooks 1975 — база > фичи",
        "- Hunicke 2004 — MDA",
        "- Skinner 1938 — variable reward",
        "- Campbell 1949 — Hero's Journey",
        "",
        "## 🗣️ ТОН",
        "",
        "- Игровой, с юмором, по делу",
        "- Аналогии: Mass Effect, Warhammer, Borderlands, Fallout",
        "- Короткие диалоги, не раздутые",
        "- Д9: не гадать — сначала диагностика",
        "",
        "## 📌 ЧТО ДЕЛАТЬ ПРЯМО СЕЙЧАС",
        "",
        f"Продолжаем с **{next_task}**.",
        "",
        "Проверка состояния:",
        "```bash",
        "cd ~/aura_project && source venv/bin/activate",
        "git log --oneline -3",
        "ruff check aura/ scripts/ 2>&1 | tail -2",
        "pytest tests/ -q --tb=line 2>&1 | tail -2",
        "python3 scripts/aura_cockpit.py",
        "```",
        "",
        "═══════════════════════════════════════════════════════════",
        "   🤖 Дядя Р2: «Капитан, копируй это в новый чат.",
        "                Я там же. Погнали.»",
        "═══════════════════════════════════════════════════════════",
    ]

    store.close()
    return "\n".join(lines)


def save_handoff(path: Path | None = None, **kwargs) -> Path:
    """Сохраняет пакет в файл и возвращает путь."""
    out = path or (Path.home() / "aura_private" / "HANDOFF.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    text = build_handoff(**kwargs)
    out.write_text(text, encoding="utf-8")
    return out


def print_handoff(**kwargs) -> str:
    """Печатает пакет в stdout — можно скопировать."""
    text = build_handoff(**kwargs)
    print(text)
    return text
