"""Registry — выбор лучшего провайдера (fallback chain).

Наука: Fallback chain (Nygard 2007), Circuit Breaker.
"""
from __future__ import annotations

from aura.inference.providers.base import LLMProvider, ProviderConfig
from aura.inference.providers.ollama import OllamaProvider
from aura.inference.providers.openai import OpenAIProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self.providers: list[LLMProvider] = []
        self._register_defaults()

    def _register_defaults(self) -> None:
        # 1. Ollama (default — локальный)
        self.providers.append(OllamaProvider(ProviderConfig(
            name="ollama", model="qwen2.5:7b-instruct-q4_K_M",
        )))
        # 2. OpenAI (если есть ключ)
        self.providers.append(OpenAIProvider(ProviderConfig(
            name="openai", model="gpt-4o-mini",
        )))
        # Задел на будущее: Gemini, Qwen, DeepSeek, Anthropic

    def available(self) -> list[str]:
        return [p.name for p in self.providers if p.is_available()]

    def ask(self, prompt: str, system: str = "") -> tuple[str | None, str]:
        """Пробует провайдеры по очереди. Возврат: (ответ, имя_провайдера)."""
        for p in self.providers:
            if not p.is_available():
                continue
            result = p.ask(prompt, system)
            if result:
                return result, p.name
        return None, "none"


_REGISTRY: ProviderRegistry | None = None


def get_registry() -> ProviderRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = ProviderRegistry()
    return _REGISTRY


__all__ = ["ProviderRegistry", "get_registry"]
