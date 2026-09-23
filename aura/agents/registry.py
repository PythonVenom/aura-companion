"""
Агент реестра памяти (AgentRegistry).

Логирует события (команды, диалоги, действия) в JSON-файл.
Показывает контекст по запросу.

Мигрирован из agents/memory_registry.py (монолит).
Изменения при миграции:
- Контракт BaseAgent: can_handle / handle (для команды "покажи память")
- log() / get_last() / get_context() — публичные методы (события)
- Логика НЕ менялась

ВАЖНО:
- memory_file НЕ меняется — путь ~/aura_project/memory_registry.json.
  Файл уже накопил историю сессий, терять нельзя.
- В тестах путь подменяется через monkeypatch.

Наука:
- Команды → can_handle / handle
- События и операции → публичные методы
- Никаких import __main__
"""

from __future__ import annotations

import json
import os
from datetime import datetime

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentRegistry(BaseAgent):
    """
    Реестр памяти.

    Обрабатывает запросы:
    - "покажи память" / "что в памяти" / "контекст"

    Плюс публичные методы:
    - log(event_type, data) — записать событие
    - get_last(count) — последние N событий
    - get_context() — контекст сессии
    """

    name = "registry"
    MODULE_ALWAYS = True

    # Путь к файлу — не меняем при миграции
    MEMORY_FILE = os.path.expanduser("~/aura_project/memory_registry.json")

    # Ключевые слова для can_handle
    KEYWORDS = (
        "покажи память",
        "что в памяти",
        "покажи контекст",
        "реестр памяти",
    )

    def __init__(self) -> None:
        self.memory_file = self.MEMORY_FILE
        self.session_data = self._load_or_create()
        self.last_event = None
        self.is_initialized = True

    # --- Публичные методы (события и операции) ---

    def log(self, event_type: str, data: dict) -> None:
        """
        Записать событие.

        Вызывается из aura_main.py после каждого ответа Ауры.
        event_type: "command", "dialog", "action".
        """
        event = {
            "time": datetime.now().isoformat(),
            "type": event_type,
            "data": data,
        }
        self.session_data["events"].append(event)
        self._save()

        if event_type == "command":
            self.session_data["summary"]["total_commands"] += 1
            cmd = data.get("command", "")
            if cmd:
                self.session_data["summary"]["most_used"][cmd] = (
                    self.session_data["summary"]["most_used"].get(cmd, 0) + 1
                )

    def get_last(self, count: int = 10) -> list:
        """Последние N событий."""
        return self.session_data["events"][-count:]

    def get_context(self) -> dict:
        """Контекст сессии: последняя команда, диалог, действие."""
        last_events = self.get_last(20)
        context = {
            "last_command": None,
            "last_dialog": None,
            "last_action": None,
            "recent_commands": [],
        }
        for e in last_events:
            if e["type"] == "command":
                context["last_command"] = e["data"].get("command")
                context["recent_commands"].append(e["data"].get("command"))
            elif e["type"] == "dialog":
                context["last_dialog"] = e["data"]
            elif e["type"] == "action":
                context["last_action"] = e["data"].get("action")
        return context

    # --- Контракт BaseAgent (команды) ---

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        cmd = request.text.lower()
        if "покажи память" in cmd or "что в памяти" in cmd:
            context_json = json.dumps(
                self.get_context(), ensure_ascii=False, indent=2
            )
            return AgentResponse.ok(
                text=context_json[:500],
                agent_name=self.name,
            )
        if "покажи контекст" in cmd or "реестр памяти" in cmd:
            context_json = json.dumps(
                self.get_context(), ensure_ascii=False, indent=2
            )
            return AgentResponse.ok(
                text=context_json[:500],
                agent_name=self.name,
            )
        return AgentResponse.not_handled(agent_name=self.name)

    # --- Внутренние методы ---

    def _load_or_create(self) -> dict:
        """Загрузить JSON-файл или создать новую сессию."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return self._new_session()
        return self._new_session()

    def _new_session(self) -> dict:
        return {
            "session_id": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            "start_time": datetime.now().isoformat(),
            "events": [],
            "summary": {
                "total_commands": 0,
                "most_used": {},
                "patterns": [],
            },
        }

    def _save(self) -> None:
        """Сохранить JSON-файл. Ошибки молча игнорируются (как в монолите)."""
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.session_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


__all__ = ["AgentRegistry"]
