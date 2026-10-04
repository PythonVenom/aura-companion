"""AgentDeepSeek — плагин для Aura (ADR-090)."""
from __future__ import annotations
import os
from aura.core.egress_broker import EgressBroker, BrokerPolicy


class AgentDeepSeek:
    name = "deepseek"
    KEYWORDS = ("спроси у дипсик", "спроси deepseek", "дипсик ", "deepseek ")
    ENDPOINT = "https://api.deepseek.com/v1/chat/completions"

    def __init__(self):
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        self.model = os.environ.get("AURA_DEEPSEEK_MODEL", "deepseek-chat")
        self.broker = EgressBroker(BrokerPolicy(
            allowed_endpoints=["api.deepseek.com"],
            daily_budget=float(os.environ.get("AURA_API_BUDGET", "100.0")),
        ))

    def can_handle(self, text: str) -> bool:
        t = text.lower()
        return any(kw in t for kw in self.KEYWORDS)

    def _extract_prompt(self, text: str) -> str:
        t = text.lower()
        for kw in self.KEYWORDS:
            if kw in t:
                idx = t.index(kw) + len(kw)
                return text[idx:].strip(" .,!?:;")
        return text

    def handle(self, text: str) -> str:
        if not self.api_key:
            return "❌ DEEPSEEK_API_KEY не установлен"
        prompt = self._extract_prompt(text)
        if not prompt:
            return "❌ Пустой запрос"
        if not self.broker.check_budget(cost=0.01):
            return "❌ Бюджет API исчерпан"
        try:
            self.broker.validate_endpoint(self.ENDPOINT)
        except PermissionError as e:
            return f"❌ {e}"
        try:
            import httpx
        except ImportError:
            return "❌ httpx не установлен"
        clean = self.broker.filter_payload({"prompt": prompt, "model": self.model})
        try:
            r = httpx.post(
                self.ENDPOINT,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": clean["model"],
                    "messages": [{"role": "user", "content": clean["prompt"]}],
                    "max_tokens": 1024,
                },
                timeout=60.0,
            )
            r.raise_for_status()
            self.broker.record_spend(0.01)
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"❌ DeepSeek: {e}"


__all__ = ["AgentDeepSeek"]
