"""Gemini — Google (нужен API-ключ)."""
from __future__ import annotations

import json
import os
import urllib.request

from aura.inference.providers.base import LLMProvider


class GeminiProvider(LLMProvider):
    name = "gemini"

    def is_available(self) -> bool:
        return bool(self.config.api_key or os.environ.get("GEMINI_API_KEY"))

    def ask(self, prompt: str, system: str = "") -> str | None:
        key = self.config.api_key or os.environ.get("GEMINI_API_KEY", "")
        if not key:
            return None
        try:
            model = self.config.model or "gemini-1.5-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            data = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "systemInstruction": {"parts": [{"text": system}]} if system else None,
            }).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=self.config.timeout) as r:
                resp = json.loads(r.read().decode())
                return resp["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return None


__all__ = ["GeminiProvider"]
