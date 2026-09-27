"""Windows: WASAPI + WinAPI. Заглушка для будущего порта (Фаза 21)."""
from __future__ import annotations


class WindowsAudio:
    def __init__(self):
        raise NotImplementedError("Windows поддержка в разработке (Фаза 21)")


class WindowsService:
    def __init__(self):
        raise NotImplementedError("Windows поддержка в разработке (Фаза 21)")


class WindowsMedia:
    def __init__(self):
        raise NotImplementedError("Windows поддержка в разработке (Фаза 21)")


__all__ = ["WindowsAudio", "WindowsService", "WindowsMedia"]
