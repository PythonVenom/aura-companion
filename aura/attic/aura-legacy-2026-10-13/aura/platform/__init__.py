"""Platform Abstraction Layer (ADR-017).

Единый интерфейс для системных вызовов. Платформа выбирается
автоматически по sys.platform + /etc/os-release.
"""
from __future__ import annotations

import sys


def _distro() -> str:
    """ID дистрибутива или '' для не-Linux."""
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("ID="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


def _is_ubuntu_like() -> bool:
    """Ubuntu / Debian / Mint / Pop."""
    d = _distro().lower()
    return d in ("ubuntu", "debian", "linuxmint", "pop", "kali", "raspbian")


def get_audio():
    """Вернуть AudioDevice текущей платформы."""
    if sys.platform.startswith("linux"):
        if _is_ubuntu_like():
            from aura.platform.ubuntu import UbuntuAudio
            return UbuntuAudio()
        from aura.platform.linux import LinuxAudio
        return LinuxAudio()
    elif sys.platform == "win32":
        from aura.platform.windows import WindowsAudio
        return WindowsAudio()
    elif sys.platform == "darwin":
        from aura.platform.macos import MacOSAudio
        return MacOSAudio()
    raise NotImplementedError(f"Platform {sys.platform} not supported yet")


def get_service():
    """Вернуть SystemService текущей платформы."""
    if sys.platform.startswith("linux"):
        if _is_ubuntu_like():
            from aura.platform.ubuntu import UbuntuService
            return UbuntuService()
        from aura.platform.linux import LinuxService
        return LinuxService()
    raise NotImplementedError(f"Platform {sys.platform} not supported yet")


def get_media():
    """Вернуть MediaController текущей платформы."""
    if sys.platform.startswith("linux"):
        if _is_ubuntu_like():
            from aura.platform.ubuntu import UbuntuMedia
            return UbuntuMedia()
        from aura.platform.linux import LinuxMedia
        return LinuxMedia()
    raise NotImplementedError(f"Platform {sys.platform} not supported yet")


__all__ = ["get_audio", "get_media", "get_service"]
