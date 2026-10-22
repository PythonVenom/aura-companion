"""
Платформенный адаптер.

Агенты НЕ вызывают xdotool/pywin32/AppKit напрямую.
Они вызывают методы PlatformAdapter. Это обеспечивает:
- Кроссплатформенность (Linux/Windows/macOS)
- Тестируемость (легко мокать)
- Изоляцию (агент не знает про ОС)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass
class WindowInfo:
    """Информация об окне."""

    id: str
    title: str
    app: str = ""
    is_active: bool = False


@runtime_checkable
class PlatformAdapter(Protocol):
    """
    Контракт платформенного адаптера.

    Реализации:
    - linux_x11.py — Linux с X11
    - linux_wayland.py — Linux с Wayland (заглушка)
    - windows.py — Windows (заглушка)
    - macos.py — macOS (заглушка)
    """

    name: str

    # --- Аудио ---
    async def get_volume(self) -> int:
        """Громкость 0-100."""
        ...

    async def set_volume(self, level: int) -> None:
        """Установить громкость 0-100."""
        ...

    async def mute(self) -> None:
        ...

    async def unmute(self) -> None:
        ...

    # --- Окна ---
    async def list_windows(self) -> list[WindowInfo]:
        ...

    async def focus_window(self, window_id: str) -> bool:
        ...

    async def close_window(self, window_id: str) -> bool:
        ...

    # --- Экран ---
    async def screenshot(self, path: Path) -> bool:
        ...

    # --- Приложения ---
    async def open_app(self, name: str) -> bool:
        ...

    # --- Уведомления ---
    async def notify(self, title: str, body: str) -> None:
        ...

    # --- Пути ---
    def config_dir(self) -> Path:
        """Директория конфигов (кроссплатформенно)."""
        ...

    def data_dir(self) -> Path:
        """Директория данных (память, vault, логи)."""
        ...


class UnsupportedPlatformError(NotImplementedError):
    """Платформа не поддерживает операцию."""

    pass


__all__ = [
    "PlatformAdapter",
    "UnsupportedPlatformError",
    "WindowInfo",
]
