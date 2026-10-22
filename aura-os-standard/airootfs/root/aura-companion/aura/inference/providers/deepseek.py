"""DeepSeek — облачный (совместим с OpenAI API)."""
from __future__ import annotations

import json
import os
import urllib.request

from aura.inference.providers.base import LLMProvider


class DeepSeekProvider(LLMProvider):
    name = "deepseek"

    def is_available(self) -> bool:
        return bool(self.config.api_key or os.environ.get("DEEPSEEK_API_KEY"))

    def ask(self, prompt: str, system: str = "") -> str | None:
        key = self.config.api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        if not key:
            return None
        try:
            data = json.dumps({
                "model": self.config.model or "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            }).encode()
            req = urllib.request.Request(
                "https://api.deepseek.com/v1/chat/completions",
                data=data,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
            )
            with urllib.request.urlopen(req, timeout=self.config.timeout) as r:
                resp = json.loads(r.read().decode())
                return resp["choices"][0]["message"]["content"]
        except Exception:
            return None


__all__ = ["DeepSeekProvider"]
