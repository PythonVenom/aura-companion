"""Wrappers для сторонних приложений (ADR-037).

Единый интерфейс для Blender, Figma, Ableton, LinuxCNC, GRBL и др.
"""
from aura.wrappers.base import AppWrapper, WrapperError
from aura.wrappers.registry import WrapperRegistry, get_registry

__all__ = ["AppWrapper", "WrapperError", "WrapperRegistry", "get_registry"]
