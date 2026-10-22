"""LLMProvider — базовый контракт для всех провайдеров."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProviderConfig:
    name: str
    model: str
    api_key: str = ""
    url: str = ""
    timeout: int = 30


class LLMProvider:
    name = "base"

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    def is_available(self) -> bool:
        raise NotImplementedError

    def ask(self, prompt: str, system: str = "") -> str | None:
        raise NotImplementedError


__all__ = ["LLMProvider", "ProviderConfig"]
