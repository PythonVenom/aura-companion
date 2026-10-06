"""Platform adapters — единый интерфейс для Aura на всех ОС.

Наука:
- POSIX (IEEE 1003.1) — базовый слой
- Hardware Abstraction Layer (Tanenbaum) — абстракция от железа
- Device Tree (devicetree.org) — описание железа на embedded

Цель: один код Aura → работает везде, где Python.
"""
from __future__ import annotations

import platform
import sys
from pathlib import Path


def detect_platform() -> dict:
    """Определить текущую платформу."""
    p = {
        "system": platform.system().lower(),
        "machine": platform.machine().lower(),
        "python": sys.version_info[:2],
        "is_wsl": "microsoft" in platform.release().lower(),
    }
    if p["system"] == "linux":
        p["family"] = "linux"
    elif p["system"] == "darwin":
        p["family"] = "macos"
    elif p["system"] == "windows":
        p["family"] = "windows"
    elif "bsd" in p["system"]:
        p["family"] = "bsd"
    else:
        p["family"] = "unknown"

    # Архитектура
    arch_map = {
        "x86_64": "x86_64", "amd64": "x86_64",
        "aarch64": "arm64", "armv7l": "arm32",
        "riscv64": "riscv64",
        "mips": "mips", "mips64": "mips64",
    }
    p["arch"] = arch_map.get(p["machine"], p["machine"])
    return p


def is_supported(platform_info: dict | None = None) -> bool:
    """Поддерживается ли эта платформа."""
    info = platform_info or detect_platform()
    return info["family"] in ("linux", "macos", "windows", "bsd")


__all__ = ["detect_platform", "is_supported"]
