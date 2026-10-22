"""AgentStringCounter — детерминированный счётчик букв/слов/символов.

Наука: не мучить LLM арифметикой (Stiennon 2020, "Learning to summarize").
Python len() всегда точнее чем токенизатор.

Примеры:
    «сколько букв в слове программирование» → 16
    «сколько слов в фразе» → N
    «сколько символов в тексте» → N
"""
from __future__ import annotations

import re

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentStringCounter(BaseAgent):
    """Считает буквы/слова/символы. Детерминированный, без LLM."""

    name = "string_counter"
    MODULE_ALWAYS = True

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(k in t for k in (
            "сколько букв в слове", "сколько букв в ",
            "сколько слов в", "сколько символов в",
        ))

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        text = request.text
        # Извлекаем слово/фразу: «...в слове X» или «...в «X»»
        target = self._extract_target(text)

        if not target:
            return AgentResponse.ok(
                text="❓ Уточните: «сколько букв в слове <X>»",
                agent_name=self.name,
            )

        t_low = text.lower()
        if "букв" in t_low:
            # Буквы = только буквы, без пробелов/знаков
            letters = sum(1 for c in target if c.isalpha())
            return AgentResponse.ok(
                text=f"📊 Букв в слове «{target}»: {letters}",
                agent_name=self.name,
            )
        if "слов" in t_low:
            words = len(target.split())
            return AgentResponse.ok(
                text=f"📊 Слов: {words}",
                agent_name=self.name,
            )
        if "символ" in t_low:
            return AgentResponse.ok(
                text=f"📊 Символов: {len(target)}",
                agent_name=self.name,
            )
        return AgentResponse.not_handled(self.name)

    @staticmethod
    def _extract_target(text: str) -> str:
        """Извлечь целевое слово/фразу из запроса."""
        # Вариант 1: «в слове программирование»
        m = re.search(r"в\s+слове\s+([а-яёa-z\-]+)", text, re.IGNORECASE)
        if m:
            return m.group(1)
        # Вариант 2: «в «программирование»»
        m = re.search(r"в\s+[«\"']([^»\"']+)[»\"']", text)
        if m:
            return m.group(1)
        # Вариант 3: «в слове «X»» (после кавычки)
        m = re.search(r"[«\"']([^»\"']+)[»\"']", text)
        if m:
            return m.group(1)
        # Вариант 4: последнее слово в запросе
        words = text.split()
        if words:
            return words[-1].strip("?.!,;:")
        return ""


__all__ = ["AgentStringCounter"]
