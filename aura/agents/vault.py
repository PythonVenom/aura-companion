"""
Агент хранилища фактов (AgentVault).

Key-value хранилище в vault.json.
Хранит факты о пользователе: «запомни мой цвет синий».

Мигрирован из agents/vault.py (монолит, мёртвый по ADR-004).
Изменения:
- Контракт BaseAgent: can_handle / handle
- Логика НЕ менялась
- vault.json — тот же путь

Портирован как заготовка (Фаза 6). НЕ подключён к bootstrap.
См. ADR-004.
"""

from __future__ import annotations

import json
import os

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentVault(BaseAgent):
    """Key-value хранилище фактов."""

    name = "vault"

    FACTS_FILE = os.path.expanduser("~/aura_project/vault.json")

    KEYWORDS = (
        "мои факты",
        "что ты знаешь",
        "покажи факты",
        "запомни",
    )

    def __init__(self) -> None:
        self.facts_file = self.FACTS_FILE
        self.facts: dict = {}
        self._load()

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        original = request.text
        cmd = original.lower().strip()

        if any(kw in cmd for kw in ("мои факты", "что ты знаешь", "покажи факты")):
            facts = self.get_all_facts()
            if not facts:
                return AgentResponse.ok(text="📭 Фактов нет", agent_name=self.name)
            lines = ["📌 Мои факты:"]
            for k, v in facts.items():
                lines.append(f"  • {k} = {v}")
            return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)

        if "запомни" in cmd:
            idx = cmd.index("запомни") + len("запомни")
            rest = original[idx:].strip()
            parts = rest.split(" ", 1)
            if len(parts) == 2:
                return AgentResponse.ok(
                    text=self.add_fact(parts[0], parts[1]),
                    agent_name=self.name,
                )
            return AgentResponse.ok(
                text="Скажи: запомни ключ значение",
                agent_name=self.name,
            )

        return AgentResponse.not_handled(agent_name=self.name)

    def add_fact(self, key: str, value: str) -> str:
        self.facts[key] = value
        self._save()
        return f"📌 Запомнила: {key} = {value}"

    def get_fact(self, key: str):
        return self.facts.get(key, None)

    def get_all_facts(self) -> dict:
        return self.facts

    def _load(self) -> None:
        if os.path.exists(self.facts_file):
            try:
                with open(self.facts_file, "r", encoding="utf-8") as f:
                    self.facts = json.load(f)
            except Exception:
                self.facts = {}

    def _save(self) -> None:
        try:
            with open(self.facts_file, "w", encoding="utf-8") as f:
                json.dump(self.facts, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


__all__ = ["AgentVault"]
