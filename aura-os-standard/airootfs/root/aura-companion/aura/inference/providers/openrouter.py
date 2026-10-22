"""OpenRouter — агрегатор 100+ моделей."""
from __future__ import annotations

import json
import os
import urllib.request

from aura.inference.providers.base import LLMProvider


class OpenRouterProvider(LLMProvider):
    name = "openrouter"

    def is_available(self) -> bool:
        return bool(self.config.api_key or os.environ.get("OPENROUTER_API_KEY"))

    def ask(self, prompt: str, system: str = "") -> str | None:
        key = self.config.api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if not key:
            return None
        try:
            data = json.dumps({
                "model": self.config.model or "meta-llama/llama-3.1-8b-instruct:free",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            }).encode()
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=data,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
            )
            with urllib.request.urlopen(req, timeout=self.config.timeout) as r:
                resp = json.loads(r.read().decode())
                return resp["choices"][0]["message"]["content"]
        except Exception:
            return None


__all__ = ["OpenRouterProvider"]
