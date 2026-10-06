"""T-os-10 — Symbiotic layer framework.

Наука:
- Adapter + Strategy (Gamma et al. 1994, GoF)
- Capability system (Dennis & Van Horn 1966)
- SPI (Service Provider Interface, Java 1998)
- Feature detection (Modernizr 2010)
- Graceful degradation (Nielsen 1993)

Идея: одна точка входа `get("windows.sapi")` → adapter или None.
Агенты работают через неё, не зная об ОС.

Feature ID: "<os>.<feature>" — напр. "windows.sapi", "macos.keychain",
"astra.mac_parsec", "linux.systemd", "android.foreground_service".
"""
from __future__ import annotations

import importlib
import platform
from pathlib import Path
from typing import Any

# Реестр: feature_id → (module_path, class_name)
REGISTRY: dict[str, tuple[str, str]] = {
    # Windows
    "windows.sapi": ("aura.os_features.windows", "SAPIAdapter"),
    "windows.wsr": ("aura.os_features.windows", "WSRAdapter"),
    "windows.hello": ("aura.os_features.windows", "HelloAdapter"),
    "windows.registry": ("aura.os_features.windows", "RegistryAdapter"),
    "windows.defender": ("aura.os_features.windows", "DefenderAdapter"),

    # macOS
    "macos.keychain": ("aura.os_features.macos", "KeychainAdapter"),
    "macos.touch_id": ("aura.os_features.macos", "TouchIDAdapter"),
    "macos.shortcuts": ("aura.os_features.macos", "ShortcutsAdapter"),
    "macos.tcc": ("aura.os_features.macos", "TCCAdapter"),

    # Astra Linux
    "astra.mac_parsec": ("aura.os_features.astra", "ParsecAdapter"),
    "astra.gost_sign": ("aura.os_features.astra", "GOSTAdapter"),

    # Linux (generic)
    "linux.systemd": ("aura.os_features.linux", "SystemdAdapter"),
    "linux.pipewire": ("aura.os_features.linux", "PipewireAdapter"),

    # Android
    "android.intents": ("aura.os_features.android", "IntentsAdapter"),
    "android.foreground": ("aura.os_features.android", "ForegroundAdapter"),

    # BSD
    "bsd.capsicum": ("aura.os_features.bsd", "CapsicumAdapter"),
    "bsd.pledge": ("aura.os_features.bsd", "PledgeAdapter"),
}


def current_os() -> str:
    """Определить ОС в терминах наших feature-префиксов."""
    sys_name = platform.system().lower()
    if sys_name == "linux":
        # Astra detection
        try:
            release = Path("/etc/os-release").read_text(encoding="utf-8")
            if "astra" in release.lower():
                return "astra"
        except Exception as e:
            # F-006: не глотать (раздел 17 промта)
            import logging
            logging.getLogger('aura.os_features').warning(
                'os_features error: %s', e)
        # Android (Termux)
        import os as _os
        if "com.termux" in _os.environ.get("PREFIX", ""):
            return "android"
        return "linux"
    if sys_name == "darwin":
        return "macos"
    if sys_name == "windows":
        return "windows"
    if "bsd" in sys_name:
        return "bsd"
    return "unknown"


def detect(feature: str) -> bool:
    """Проверить доступна ли feature. Feature detection (Modernizr 2010).

    Пример:
        detect("windows.sapi")  # True если Windows + SAPI доступен
        detect("astra.mac_parsec")  # False если не Astra
    """
    if "." not in feature:
        return False
    os_prefix = feature.split(".", 1)[0]
    if os_prefix != current_os():
        return False
    return feature in REGISTRY


def get(feature: str) -> Any | None:
    """Получить adapter для feature. None если недоступен (graceful).

    Пример:
        sapi = get("windows.sapi")
        if sapi:
            sapi.speak("Привет")

    Наука: Dennis & Van Horn 1966 — capability-based, не проверка роли.
    """
    if not detect(feature):
        return None
    module_path, class_name = REGISTRY[feature]
    try:
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        return cls()
    except (ImportError, AttributeError):
        return None


def list_available() -> dict[str, bool]:
    """Все features текущей ОС и их доступность."""
    return {
        fid: detect(fid)
        for fid in REGISTRY
        if fid.startswith(f"{current_os()}.")
    }


def list_all() -> dict[str, dict[str, bool]]:
    """Все features всех ОС: {os: {feature: available}}."""
    result: dict[str, dict[str, bool]] = {}
    for fid in REGISTRY:
        os_prefix = fid.split(".", 1)[0]
        result.setdefault(os_prefix, {})[fid] = detect(fid)
    return result


def safe_call(feature: str, method: str, *args, default: Any = None, **kwargs) -> Any:
    """Безопасно вызвать метод adapter. Fallback — default.

    Graceful degradation (Nielsen 1993): если feature нет — не падаем.

    Пример:
        safe_call("windows.sapi", "speak", "Привет", default=False)
    """
    adapter = get(feature)
    if adapter is None:
        return default
    fn = getattr(adapter, method, None)
    if fn is None:
        return default
    try:
        return fn(*args, **kwargs)
    except Exception:
        return default


def status() -> dict:
    """Публичный API: сводка для диагностики."""
    os_name = current_os()
    available = list_available()
    return {
        "os": os_name,
        "features_registered": len([f for f in REGISTRY if f.startswith(f"{os_name}.")]),
        "features_available": sum(1 for v in available.values() if v),
        "available": available,
        "registry_total": len(REGISTRY),
    }


__all__ = [
    "REGISTRY",
    "current_os",
    "detect",
    "get",
    "list_all",
    "list_available",
    "safe_call",
    "status",
]
