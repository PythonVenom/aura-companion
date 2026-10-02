"""
Агент менеджера задач (AgentTaskManager).

JSON-хранилище задач в tasks.json.
Задачи: add, list, plan.

Мигрирован из agents/task_manager.py (монолит, мёртвый по ADR-004).
Изменения:
- Контракт BaseAgent: can_handle / handle
- Логика НЕ менялась
- tasks.json — тот же путь

Портирован как заготовка (Фаза 6). НЕ подключён к bootstrap.
См. ADR-004.

ВОЗМОЖНЫЙ ДУБЛЬ: journal уже умеет задачи (markdown, [ ]/[x]).
Решить при подключении: нужен ли второй формат.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentTaskManager(BaseAgent):
    """JSON-менеджер задач."""

    name = "task_manager"

    TASKS_FILE = str(__import__("aura.paths", fromlist=["CACHE_DIR"]).CACHE_DIR / "tasks.json")

    KEYWORDS = (
        "мои задачи",
        "список задач",
        "план на сегодня",
        "добавь задачу",
        "запиши задачу",
    )

    def __init__(self) -> None:
        self.tasks: dict = {}
        self.tasks_file = self.TASKS_FILE
        self._load()

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        original = request.text
        cmd = original.lower().strip()

        if "план на сегодня" in cmd:
            return AgentResponse.ok(text=self.get_plan(), agent_name=self.name)

        if any(kw in cmd for kw in ("мои задачи", "список задач")):
            return AgentResponse.ok(text=self.get_tasks(), agent_name=self.name)

        if "добавь задачу" in cmd or "запиши задачу" in cmd:
            for word in ("добавь задачу", "запиши задачу"):
                idx = cmd.find(word)
                if idx >= 0:
                    rest = original[idx + len(word):].strip()
                    if rest:
                        return AgentResponse.ok(
                            text=self.add_task(rest),
                            agent_name=self.name,
                        )
                    return AgentResponse.ok(
                        text="Что добавить?",
                        agent_name=self.name,
                    )

        return AgentResponse.not_handled(agent_name=self.name)

    def add_task(self, task: str) -> str:
        self.tasks[datetime.now().isoformat()] = task
        self._save()
        return f"✅ Добавила задачу: {task}"

    def get_tasks(self) -> str:
        if not self.tasks:
            return "📋 Задач нет, создатель. Добавить что-то?"
        tasks = list(self.tasks.values())[-5:]
        result = "📋 Вот твои задачи:\n"
        for i, task in enumerate(tasks, 1):
            result += f"  {i}. {task}\n"
        return result

    def get_plan(self) -> str:
        if not self.tasks:
            return "📋 Задач нет."
        first = list(self.tasks.values())[0]
        return f"📋 Сегодня {len(self.tasks)} задач. Начнём с первой: {first}?"

    def _load(self) -> None:
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
            except Exception:
                self.tasks = {}

    def _save(self) -> None:
        try:
            with open(self.tasks_file, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


__all__ = ["AgentTaskManager"]
