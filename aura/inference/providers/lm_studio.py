"""LM Studio — локальный, OpenAI-совместимый API на :1234."""
from __future__ import annotations

import json
import urllib.request

from aura.inference.providers.base import LLMProvider


class LMStudioProvider(LLMProvider):
    name = "lm_studio"

    def is_available(self) -> bool:
        try:
            r = urllib.request.urlopen("http://localhost:1234/v1/models", timeout=2)
            return r.status == 200
        except Exception:
            return False

    def ask(self, prompt: str, system: str = "") -> str | None:
        try:
            data = json.dumps({
                "model": self.config.model or "local-model",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            }).encode()
            req = urllib.request.Request(
                "http://localhost:1234/v1/chat/completions",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=self.config.timeout) as r:
                resp = json.loads(r.read().decode())
                return resp["choices"][0]["message"]["content"]
        except Exception:
            return None


__all__ = ["LMStudioProvider"]
