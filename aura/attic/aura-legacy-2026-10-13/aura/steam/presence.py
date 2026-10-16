"""Steam Rich Presence — статус Aura в Steam.

Требует:
  1. Steamworks SDK (https://partner.steamgames.com)
  2. Зарегистрированное приложение (App ID)
  3. pip install steamworks

Пока SDK нет — модуль работает как заглушка.
"""
from __future__ import annotations

import contextlib
from pathlib import Path

# Проверка наличия SDK
HAS_STEAM = False
try:
    import steamworks  # type: ignore
    HAS_STEAM = True
except ImportError:
    pass

# Конфиг для future
STEAM_APP_ID = 0  # заполнить после регистрации
STEAM_CONFIG = Path.home() / ".config" / "aura" / "steam.toml"


def is_configured() -> bool:
    """SDK есть И App ID заполнен."""
    return HAS_STEAM and STEAM_APP_ID > 0


def set_aura_status(
    sector: str = "STABILIZE",
    xp: int = 0,
    rank: str = "Кадет",
) -> bool:
    """Установить статус в Steam. True если успешно."""
    if not is_configured():
        return False
    with contextlib.suppress(Exception):
        steam = steamworks.Steam()
        steam.set_rich_presence("steam_display", "#Status")
        steam.set_rich_presence("sector", sector)
        steam.set_rich_presence("xp", str(xp))
        steam.set_rich_presence("rank", rank)
        return True
    return False


def clear_aura_status() -> bool:
    """Сбросить статус."""
    if not is_configured():
        return False
    with contextlib.suppress(Exception):
        steam = steamworks.Steam()
        steam.clear_rich_presence()
        return True
    return False


__all__ = [
    "HAS_STEAM", "STEAM_APP_ID",
    "clear_aura_status", "is_configured", "set_aura_status",
]
