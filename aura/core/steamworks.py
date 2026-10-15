"""Steamworks SDK wrapper (Python).

Наука: Valve Steamworks API, ctypes-обёртка.
Fallback: если steam не запущен — работает standalone.
"""
from __future__ import annotations

import os
from pathlib import Path

APP_ID = "480"  # Spacewar (тестовый app_id)


class SteamworksWrapper:
    """Минимальная обёртка Steamworks API."""

    def __init__(self, app_id: str = APP_ID) -> None:
        self.app_id = app_id
        self._ready = False
        self._steam = None
        # Индикатор, что steamworkspy установлен
        try:
            import steamworks  # noqa: F401
            self._ready = True
        except ImportError:
            pass

    @property
    def ready(self) -> bool:
        return self._ready

    def init(self) -> bool:
        """Инициализация. Создаёт steam_appid.txt."""
        try:
            Path("steam_appid.txt").write_text(self.app_id)
        except Exception:
            pass
        if self._ready:
            try:
                import steamworks
                self._steam = steamworks.Steam()
                return self._steam.init()
            except Exception:
                return False
        return False

    def unlock_achievement(self, name: str) -> bool:
        """Разблокировать достижение."""
        if not self._steam:
            return False
        try:
            self._steam.UserStats.SetAchievement(name)
            self._steam.UserStats.StoreStats()
            return True
        except Exception:
            return False

    def set_stat(self, name: str, value: int) -> bool:
        """Установить статистику."""
        if not self._steam:
            return False
        try:
            self._steam.UserStats.SetStat(name, value)
            self._steam.UserStats.StoreStats()
            return True
        except Exception:
            return False

    def is_steam_running(self) -> bool:
        """Запущен ли Steam?"""
        # Проверка через переменную окружения
        return bool(os.environ.get("SteamAppId") or os.environ.get("SteamGameId"))


_STEAM: SteamworksWrapper | None = None


def get_steam() -> SteamworksWrapper:
    global _STEAM
    if _STEAM is None:
        _STEAM = SteamworksWrapper()
    return _STEAM


__all__ = ["APP_ID", "SteamworksWrapper", "get_steam"]
