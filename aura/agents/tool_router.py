"""
Агент маршрутизатора инструментов (AgentToolRouter).

LLM сама решает, какой инструмент вызвать, через tool calling.
Ollama, модель qwen2.5:7b-instruct-q4_K_M.

Мигрирован из agents/tool_router.py (монолит).
Упрощён по сравнению с монолитом:
- Убран regex-fallback <tool> <json> (qwen2.5 умеет structured tool_calls)
- Убран execute (Orchestrator зовёт route напрямую)
- Убран print при загрузке
- НЕ наследует BaseAgent (сервис, не агент)

См. ADR-005.
"""

from __future__ import annotations

import json
import urllib.request


class AgentToolRouter:
    """LLM-маршрутизатор инструментов."""

    MODEL = "qwen2.5:7b-instruct-q4_K_M"
    OLLAMA_URL = "http://localhost:11434/api/chat"
    TIMEOUT = 30

    SYSTEM_PROMPT = (
        "Ты — Аура, семейный ИИ-компаньон. У тебя есть инструменты (tools).\\n\\n"
        "ПРАВИЛА ВЫБОРА ИНСТРУМЕНТА:\\n"
        "1. Если команда — просьба сделать действие — вызови ПОДХОДЯЩИЙ инструмент.\\n"
        "2. Какие песни, какая музыка, список музыки -> list_music\\n"
        "3. Какие фильмы, список фильмов -> list_movies\\n"
        "4. Включи песню X, включи трек X -> play_music с query=X\\n"
        "5. Включи фильм X -> play_movie с query=X\\n"
        "6. Открой X (приложение) -> open_app с name=X\\n"
        "7. Какие функции, что ты умеешь -> list_functions\\n"
        "8. Открой вк, открой вконтакте -> open_vk\\n"
        "9. Заблокируй экран -> lock_screen\\n"
        "10. Выключи пк -> power_off\\n\\n"
        "ЗАПРЕЩЕНО:\\n"
        "- Вызывать инструмент, если команда НЕПОНЯТНА или ОБРЕЗАНА.\\n"
        "- Вызывать list_functions, если пользователь НЕ просит функции.\\n"
        "- Угадывать. Если не уверена — ответь текстом Не поняла команду.\\n\\n"
        "Отвечай ВСЕГДА на русском. Будь краткой."
    )

    def __init__(self) -> None:
        self.tools: dict = {}
        self.tool_defs: list = []

    def register(self, name, description, parameters, handler) -> None:
        """Зарегистрировать инструмент."""
        self.tools[name] = handler
        self.tool_defs.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {p: {"type": t} for p, t in parameters.items()},
                    "required": list(parameters.keys()),
                },
            },
        })

    def route(self, user_text: str) -> dict | None:
        """LLM решает, какой инструмент вызвать."""
        if not self.tool_defs:
            return None

        try:
            data = json.dumps({
                "model": self.MODEL,
                "messages": [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                ],
                "tools": self.tool_defs,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 150},
            }).encode("utf-8")

            req = urllib.request.Request(
                self.OLLAMA_URL,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as response:
                result = json.loads(response.read().decode("utf-8"))

            message = result.get("message", {})
            tool_calls = message.get("tool_calls", [])

            if not tool_calls:
                return {"type": "text", "response": message.get("content", "")}

            call = tool_calls[0]
            func_name = call["function"]["name"]
            func_args = call["function"].get("arguments", {})

            if isinstance(func_args, str):
                try:
                    func_args = json.loads(func_args)
                except Exception:
                    func_args = {}

            if func_name not in self.tools:
                return {
                    "type": "error",
                    "response": f"❌ Инструмент {func_name} не найден",
                }

            handler = self.tools[func_name]
            try:
                result_text = handler(**func_args)
            except Exception as e:
                result_text = f"❌ Ошибка вызова {func_name}: {e}"

            return {
                "type": "tool",
                "tool": func_name,
                "args": func_args,
                "response": result_text,
            }

        except Exception as e:
            return {"type": "error", "response": f"❌ Ошибка ToolRouter: {e}"}


__all__ = ["AgentToolRouter"]
