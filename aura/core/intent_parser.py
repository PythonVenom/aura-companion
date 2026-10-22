"""Intent Parser — декомпозиция сложных целей на шаги агентов.

Использует Ollama (qwen2.5) для разбиения высокоуровневых команд
на последовательность вызовов конкретных агентов (JSON).
"""
from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any

log = logging.getLogger("aura.intent_parser")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"

PROMPT_TEMPLATE = """Ты — планировщик AuraOS. Твоя задача — разбить цель пользователя на последовательность шагов.
Доступные агенты (используй только эти id):
- window_manager: управление окнами
- app_launcher: запуск приложений (например: "запусти код", "открой браузер")
- music_local: включить музыку (например: "включи музыку")
- focus_switch: переключить режим фокуса
- system_control: управление питанием

Цель пользователя: "{text}"

Ответь СТРОГО в формате JSON без markdown:
{{"goal": "краткое описание", "steps": [{{"agent": "id_агента", "text": "конкретная команда для этого агента"}}]}}

Пример:
Пользователь: "хочу поработать, запусти код и включи музыку"
Ответ: {{"goal": "рабочая среда", "steps": [{{"agent": "app_launcher", "text": "запусти код"}}, {{"agent": "music_local", "text": "включи музыку"}}]}}

Если цель простая или не требует декомпозиции, верни: {{"goal": "none", "steps": []}}
"""

class IntentParser:
    def __init__(self, model: str = MODEL):
        self.model = model

    def parse(self, text: str) -> dict[str, Any]:
        prompt = PROMPT_TEMPLATE.format(text=text)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1}
        }
        
        try:
            req = urllib.request.Request(
                OLLAMA_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=20) as r:
                res = json.loads(r.read().decode("utf-8"))
                raw_response = res.get("response", "{}")
                plan = json.loads(raw_response)
                return plan
        except Exception as e:
            log.error(f"IntentParser failed: {e}")
            return {"goal": "none", "steps": []}

__all__ = ["IntentParser"]
