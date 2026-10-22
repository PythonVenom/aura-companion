"""Ollama — локальный провайдер (default для AURA)."""
from __future__ import annotations

import json
import urllib.request

from aura.inference.providers.base import LLMProvider


class OllamaProvider(LLMProvider):
    name = "ollama"

    def is_available(self) -> bool:
        try:
            r = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
            return r.status == 200
        except Exception:
            return False

    def ask(self, prompt: str, system: str = "") -> str | None:
        try:
            data = json.dumps({
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            }).encode()
            req = urllib.request.Request(
                "http://localhost:11434/api/chat",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=self.config.timeout) as r:
                resp = json.loads(r.read().decode())
                return resp.get("message", {}).get("content", "")
        except Exception:
            return None


__all__ = ["OllamaProvider"]
