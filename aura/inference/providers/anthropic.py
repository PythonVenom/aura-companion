"""Anthropic Claude — облачный."""
from __future__ import annotations

import json
import os
import urllib.request

from aura.inference.providers.base import LLMProvider


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def is_available(self) -> bool:
        return bool(self.config.api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def ask(self, prompt: str, system: str = "") -> str | None:
        key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            return None
        try:
            data = json.dumps({
                "model": self.config.model or "claude-3-5-sonnet-20241022",
                "max_tokens": 1024,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            }).encode()
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                },
            )
            with urllib.request.urlopen(req, timeout=self.config.timeout) as r:
                resp = json.loads(r.read().decode())
                return resp["content"][0]["text"]
        except Exception:
            return None


__all__ = ["AnthropicProvider"]
