"""Factory — выбрать адаптер по текущей ОС."""
from __future__ import annotations
import os
import platform as _plat
from aura.platform_adapters.base import BasePlatform


def get_platform() -> BasePlatform:
    sys_name = _plat.system().lower()
    if sys_name == "linux":
        # Termux → Android HAL
        if "com.termux" in os.environ.get("PREFIX", ""):
            from aura.platform_adapters.android import AndroidPlatform
            return AndroidPlatform()
        from aura.platform_adapters.linux import LinuxPlatform
        return LinuxPlatform()
    if sys_name == "darwin":
        from aura.platform_adapters.macos import MacOSPlatform
        return MacOSPlatform()
    # TODO: T-port-3 — Windows, T-port-6 — BSD
    from aura.platform_adapters.linux import LinuxPlatform
    return LinuxPlatform()


__all__ = ["get_platform"]
