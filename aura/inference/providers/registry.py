"""ProviderRegistry — fallback chain из 8 провайдеров.

Наука: Fallback chain (Nygard 2007), Circuit Breaker.
Порядок: локальные → облачные.
"""
from __future__ import annotations

from aura.inference.providers.anthropic import AnthropicProvider
from aura.inference.providers.base import LLMProvider, ProviderConfig
from aura.inference.providers.deepseek import DeepSeekProvider
from aura.inference.providers.gemini import GeminiProvider
from aura.inference.providers.lm_studio import LMStudioProvider
from aura.inference.providers.ollama import OllamaProvider
from aura.inference.providers.openai import OpenAIProvider
from aura.inference.providers.openrouter import OpenRouterProvider
from aura.inference.providers.qwen import QwenProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self.providers: list[LLMProvider] = []
        self._register_defaults()

    def _register_defaults(self) -> None:
        # Локальные (приоритет)
        self.providers.append(OllamaProvider(ProviderConfig(
            name="ollama", model="qwen2.5:7b-instruct-q4_K_M",
        )))
        self.providers.append(LMStudioProvider(ProviderConfig(
            name="lm_studio", model="local-model",
        )))
        # Облачные (если есть ключи)
        self.providers.append(OpenAIProvider(ProviderConfig(
            name="openai", model="gpt-4o-mini",
        )))
        self.providers.append(AnthropicProvider(ProviderConfig(
            name="anthropic", model="claude-3-5-sonnet-20241022",
        )))
        self.providers.append(GeminiProvider(ProviderConfig(
            name="gemini", model="gemini-1.5-flash",
        )))
        self.providers.append(DeepSeekProvider(ProviderConfig(
            name="deepseek", model="deepseek-chat",
        )))
        self.providers.append(QwenProvider(ProviderConfig(
            name="qwen", model="qwen-plus",
        )))
        self.providers.append(OpenRouterProvider(ProviderConfig(
            name="openrouter", model="meta-llama/llama-3.1-8b-instruct:free",
        )))

    def available(self) -> list[str]:
        return [p.name for p in self.providers if p.is_available()]

    def ask(self, prompt: str, system: str = "") -> tuple[str | None, str]:
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
