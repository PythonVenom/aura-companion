"""
Агент мозга (AgentBrain).

LLM-фолбэк: если реестр и tool_router не справились — brain.ask().
Ollama, модель qwen2.5:7b-instruct-q4_K_M.

Мигрирован из agents/brain.py (монолит).
Изменения при миграции:
- НЕ наследует BaseAgent (сервис, не агент)
- Убран get_latest_response (мёртвый метод)
- Убран execute (Orchestrator зовёт ask напрямую)
- Убран импорт agents.base

Наука:
- Сервис не знает про оркестратор
- Вызывается через asyncio.to_thread (синхронный)
- Тесты — на моках urllib, без живого Ollama

См. ADR-005.
"""

from __future__ import annotations

import json
import urllib.request


class AgentBrain:
    """
    LLM-фолбэк Ауры.

    Публичный метод: ask(question) -> str.
    """

    OLLAMA_URL = "http://localhost:11434/api/chat"
    MODEL = "qwen2.5:7b-instruct-q4_K_M"
    TIMEOUT = 30
    MAX_HISTORY = 10

    SYSTEM_PROMPT = (
        "Ты — Аура, семейный ИИ-компаньон. "
        "Отвечай ВСЕГДА на русском языке. "
        "НИКОГДА не используй китайский, английский или другие языки. "
        "Будь дружелюбной, без подхалимства.\n\n"
        "ПРАВИЛА:\n"
        "1. Если просят рассказать историю, сказку, анекдот — расскажи развёрнуто (10-20 предложений).\n"
        "2. Если задают простой вопрос — ответь кратко (1-3 предложения).\n"
        "3. Если просят объяснить — объясни понятно, но без воды."
    )

    def __init__(self) -> None:
        self.context_history: list[dict] = []

    def ask(self, question: str) -> str:
        """
        Спросить у LLM. Возвращает текст ответа или сообщение об ошибке.

        Ведёт историю последних MAX_HISTORY сообщений.
        """
        try:
            self.context_history.append({"role": "user", "content": question})
            if len(self.context_history) > self.MAX_HISTORY:
                self.context_history = self.context_history[-self.MAX_HISTORY:]

            messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
            messages.extend(self.context_history)

            data = json.dumps({
                "model": self.MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 700,
                    "num_ctx": 4096,
                },
            }).encode("utf-8")

            req = urllib.request.Request(
                self.OLLAMA_URL,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as response:
                result = json.loads(response.read().decode("utf-8"))
                response_text = result.get("message", {}).get(
                    "content", "Я не поняла вопрос."
                )
                self.context_history.append(
                    {"role": "assistant", "content": response_text}
                )
                return response_text
        except Exception as e:
            return f"❌ Ошибка: {e}"


__all__ = ["AgentBrain"]
