"""AppWrapper — базовый интерфейс (ADR-037).

Science: единый контракт → легко добавить новый App (Open/Closed).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class WrapperError(Exception):
    """Базовая ошибка wrapper'а."""


class AppWrapper(ABC):
    """Интерфейс обёртки над сторонним приложением."""

    name: str = ""           # "blender", "figma", "grbl"
    version: str = ""        # "4.2+"
    transport: str = ""      # "tcp", "serial", "rest", "osc", "lpd"

    def __init__(self) -> None:
        self._connected = False
        self._safe_commands: frozenset[str] = frozenset()

    @abstractmethod
    def is_available(self) -> bool:
        """Приложение установлено и доступно?"""

    @abstractmethod
    def connect(self) -> bool:
        """Установить соединение."""

    @abstractmethod
    def disconnect(self) -> None:
        """Закрыть соединение."""

    @abstractmethod
    def execute(self, cmd: str, params: dict[str, Any] | None = None) -> dict:
        """Выполнить команду. Возвращает {"ok": bool, "result": Any}."""

    def is_safe(self, cmd: str) -> bool:
        """Команда в whitelist? (ADR-037: confirm для destructive)."""
        return cmd in self._safe_commands

    def status(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "transport": self.transport,
            "connected": self._connected,
            "available": self.is_available(),
        }

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r} connected={self._connected}>"


__all__ = ["AppWrapper", "WrapperError"]
