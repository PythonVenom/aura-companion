"""Factory — выбрать адаптер по текущей ОС."""
from __future__ import annotations
import platform as _plat
from aura.platform_adapters.base import BasePlatform


def get_platform() -> BasePlatform:
    sys_name = _plat.system().lower()
    if sys_name == "linux":
        from aura.platform_adapters.linux import LinuxPlatform
        return LinuxPlatform()
    # Заглушки для будущих платформ (T-port-3..6)
    from aura.platform_adapters.linux import LinuxPlatform
    return LinuxPlatform()


__all__ = ["get_platform"]
