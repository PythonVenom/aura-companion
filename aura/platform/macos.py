"""macOS: CoreAudio + AVFoundation. Заглушка для будущего порта (Фаза 23)."""
from __future__ import annotations


class MacOSAudio:
    def __init__(self):
        raise NotImplementedError("macOS поддержка в разработке (Фаза 23)")


class MacOSService:
    def __init__(self):
        raise NotImplementedError("macOS поддержка в разработке (Фаза 23)")


class MacOSMedia:
    def __init__(self):
        raise NotImplementedError("macOS поддержка в разработке (Фаза 23)")


__all__ = ["MacOSAudio", "MacOSService", "MacOSMedia"]
