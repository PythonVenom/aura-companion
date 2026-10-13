"""Translate — переводит фразы через локальную LLM.

Использование:
    translate("Привет, капитан")  # → "Hello, captain"
    translate("Мостик", to="en")
"""

from __future__ import annotations

import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b-instruct-q4_K_M"


def translate(text: str, to: str = "en", from_: str = "ru") -> str:
    """Перевести через локальную LLM. Оффлайн, без API."""
    prompt = (
        f"Translate from {from_} to {to}. "
        f"Output ONLY the translation, no explanations:\n\n{text}"
    )
    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps({
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            return data.get("response", "").strip()
    except Exception as e:
        return f"[translate error: {e}]"


__all__ = ["translate"]
