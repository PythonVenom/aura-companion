"""
Агент авто-дневника.

Пишет все диалоги в Markdown-журнал, группирует по дням,
поддерживает задачи [ ] / [x], показывает последнюю сессию.

Мигрирован из agents/journal.py (монолит).
Изменения при миграции:
- Контракт BaseAgent: can_handle / handle (для команд пользователя)
- log_dialog() остаётся публичным методом — его дёргает aura_main.py
  после каждого ответа Ауры. Это событие, а не команда.
- get_last_session() — публичный, для показа при старте.
- add_task() / close_task() / get_pending_tasks() — публичные.

ВАЖНО:
- journal_file НЕ меняется — путь ~/aura_project/JOURNAL.md.
  Файл уже накопил историю, терять нельзя.
- Формат markdown НЕ меняется — иначе старые записи перестанут
  читаться регулярками.
- Файл коммитится в git (техдолг, отдельная задача).

Наука:
- Команды → can_handle / handle
- События и операции → публичные методы
- Никаких import __main__
"""

from __future__ import annotations

import os
import re
from datetime import datetime

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentJournal(BaseAgent):
    """
    Авто-дневник Ауры.

    Обрабатывает запросы:
    - "покажи журнал" / "что я делал" / "что было"
    - "что осталось" / "что не сделано" / "список задач"
    - "добавь задачу X" / "запиши задачу X"
    - "закрой задачу X" / "выполнил X" / "сделал X"
    - "статистика журнала"

    Плюс публичные методы:
    - log_dialog(user, aura) — событие, вызывается главным циклом
    - get_last_session() — для показа прошлой сессии при старте
    - add_task(task), close_task(task) — операции
    """

    name = "journal"
    MODULE_ALWAYS = True

    # Путь к журналу — не меняем при миграции
    JOURNAL_FILE = str(__import__("aura.paths", fromlist=["CACHE_DIR"]).CACHE_DIR / "JOURNAL.md")

    # Ключевые слова для can_handle
    SHOW_KEYWORDS = ("покажи журнал", "что я делал", "что было")
    PENDING_KEYWORDS = ("что осталось", "что не сделано", "список задач")
    ADD_KEYWORDS = ("добавь задачу", "запиши задачу", "добавь в журнал")
    CLOSE_KEYWORDS = ("закрой задачу", "выполнил", "сделал")
    STATS_KEYWORDS = ("статистика журнала",)

    def __init__(self) -> None:
        self.ready = True
        self.journal_file = self.JOURNAL_FILE
        self._ensure_file()

    # --- Публичные методы (события и операции) ---

    def log_dialog(self, user_text: str, aura_response: str) -> str:
        """
        Записать диалог в журнал.

        Вызывается из aura_main.py после каждого ответа Ауры.
        Возвращает текст статуса для логирования.
        """
        if not self.ready:
            return "❌ Журнал не готов"

        try:
            self._add_today_header()

            time_str = datetime.now().strftime("%H:%M")
            user_short = user_text[:100].strip()
            aura_short = aura_response[:150].strip()

            with open(self.journal_file, "a", encoding="utf-8") as f:
                f.write(f"### {time_str} — {user_short}\n")
                f.write(f"> {aura_short}\n\n")

            return "📔 Записала в журнал"
        except Exception as e:
            return f"❌ Ошибка журнала: {e}"

    def get_last_session(self) -> dict | None:
        """Информация о последней сессии (для показа при старте)."""
        if not os.path.exists(self.journal_file):
            return None

        with open(self.journal_file, "r", encoding="utf-8") as f:
            content = f.read()

        dates = re.findall(r"## (\d{4}-\d{2}-\d{2})", content)
        if not dates:
            return None

        last_date = dates[-1]
        today = datetime.now().strftime("%Y-%m-%d")

        times = re.findall(r"### (\d{2}:\d{2})", content)
        last_time = times[-1] if times else "неизвестно"

        pending = self.get_pending_tasks()

        return {
            "date": last_date,
            "time": last_time,
            "is_today": last_date == today,
            "pending": pending[:5],
            "pending_count": len(pending),
        }

    def add_task(self, task: str) -> str:
        """Добавить задачу в журнал."""
        if not self.ready:
            return "❌ Журнал не готов"

        try:
            self._add_today_header()

            with open(self.journal_file, "a", encoding="utf-8") as f:
                f.write(f"- [ ] {task}\n")

            return f"✅ Добавила задачу: {task}"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def close_task(self, task_text: str) -> str:
        """Отметить задачу выполненной."""
        if not self.ready:
            return "❌ Журнал не готов"

        try:
            with open(self.journal_file, "r", encoding="utf-8") as f:
                content = f.read()

            pattern = rf"- \[ \] ({re.escape(task_text)}.*)"
            new_content, count = re.subn(
                pattern, r"- [x] \1", content, flags=re.IGNORECASE
            )

            if count == 0:
                return f"❌ Задача не найдена: {task_text}"

            with open(self.journal_file, "w", encoding="utf-8") as f:
                f.write(new_content)

            return f"✅ Задача закрыта: {task_text}"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def get_pending_tasks(self) -> list[str]:
        """Список невыполненных задач."""
        if not os.path.exists(self.journal_file):
            return []

        with open(self.journal_file, "r", encoding="utf-8") as f:
            content = f.read()

        return re.findall(r"- \[ \] (.+)", content)

    def get_done_tasks(self) -> list[str]:
        """Список выполненных задач."""
        if not os.path.exists(self.journal_file):
            return []

        with open(self.journal_file, "r", encoding="utf-8") as f:
            content = f.read()

        return re.findall(r"- \[x\] (.+)", content, flags=re.IGNORECASE)

    def show_pending(self) -> str:
        """Показать невыполненные задачи."""
        pending = self.get_pending_tasks()
        if not pending:
            return "✅ Невыполненных задач нет!"

        result = f"📋 Осталось задач: {len(pending)}\n\n"
        for i, task in enumerate(pending, 1):
            result += f"{i}. [ ] {task}\n"

        return result

    def show_journal(self, days: int = 3) -> str:
        """Показать последние N дней журнала."""
        if not os.path.exists(self.journal_file):
            return "📔 Журнал пуст"

        with open(self.journal_file, "r", encoding="utf-8") as f:
            content = f.read()

        parts = re.split(r"\n## ", content)
        if len(parts) <= 1:
            return content[:1000]

        recent = parts[-(days + 1):]
        result = f"📔 Последние {days} дней:\n\n"
        for part in recent:
            result += "## " + part.strip() + "\n\n"

        return result[:2000]

    # --- Контракт BaseAgent (команды) ---

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(
            kw in text
            for kw in (
                self.SHOW_KEYWORDS
                + self.PENDING_KEYWORDS
                + self.ADD_KEYWORDS
                + self.CLOSE_KEYWORDS
                + self.STATS_KEYWORDS
            )
        )

    async def handle(self, request: AgentRequest) -> AgentResponse:
        cmd = request.text.lower().strip()

        if any(kw in cmd for kw in self.SHOW_KEYWORDS):
            session = self.get_last_session()
            if session:
                result = f"📔 Последняя сессия: {session['date']} в {session['time']}\n"
                if not session["is_today"]:
                    result += "⚠️ Это было не сегодня!\n"
                result += f"\n📋 Осталось задач: {session['pending_count']}\n"
                for task in session["pending"]:
                    result += f"  • [ ] {task}\n"
                return AgentResponse.ok(text=result, agent_name=self.name)
            return AgentResponse.ok(text="📔 Журнал пуст", agent_name=self.name)

        if any(kw in cmd for kw in self.PENDING_KEYWORDS):
            return AgentResponse.ok(
                text=self.show_pending(), agent_name=self.name
            )

        if any(kw in cmd for kw in self.ADD_KEYWORDS):
            task = cmd
            for word in ["добавь задачу", "запиши задачу", "добавь в журнал"]:
                task = task.replace(word, "")
            task = task.strip()
            if not task:
                return AgentResponse.ok(text="Что добавить?", agent_name=self.name)
            return AgentResponse.ok(
                text=self.add_task(task), agent_name=self.name
            )

        if any(kw in cmd for kw in self.CLOSE_KEYWORDS):
            task = cmd
            for word in ["закрой задачу", "выполнил", "сделал"]:
                task = task.replace(word, "")
            task = task.strip()
            if not task:
                return AgentResponse.ok(text="Что закрыть?", agent_name=self.name)
            return AgentResponse.ok(
                text=self.close_task(task), agent_name=self.name
            )

        if any(kw in cmd for kw in self.STATS_KEYWORDS):
            pending = len(self.get_pending_tasks())
            done = len(self.get_done_tasks())
            return AgentResponse.ok(
                text=f"📔 Журнал: ✅ {done} сделано, 📋 {pending} осталось",
                agent_name=self.name,
            )

        return AgentResponse.not_handled(agent_name=self.name)

    # --- Внутренние методы ---

    def _ensure_file(self) -> None:
        """Создать файл, если его нет."""
        if not os.path.exists(self.journal_file):
            with open(self.journal_file, "w", encoding="utf-8") as f:
                f.write("# 📔 Журнал Ауры\n\n")
                f.write("Автоматический дневник работы. Каждый диалог записывается сюда.\n\n")
                f.write("Формат задач:\n")
                f.write("- `[ ]` — не сделано\n")
                f.write("- `[x]` — сделано\n\n")

    def _today_header(self) -> str:
        """Заголовок сегодняшнего дня."""
        today = datetime.now().strftime("%Y-%m-%d")
        return f"## {today}"

    def _has_today_header(self) -> bool:
        """Есть ли уже заголовок сегодняшнего дня."""
        if not os.path.exists(self.journal_file):
            return False
        with open(self.journal_file, "r", encoding="utf-8") as f:
            content = f.read()
        return self._today_header() in content

    def _add_today_header(self) -> None:
        """Добавить заголовок сегодняшнего дня, если его нет."""
        if not self._has_today_header():
            with open(self.journal_file, "a", encoding="utf-8") as f:
                f.write(f"\n{self._today_header()}\n\n")


__all__ = ["AgentJournal"]
