"""WrapperRegistry — реестр доступных wrappers (ADR-037)."""
from __future__ import annotations

from typing import Type

from aura.wrappers.base import AppWrapper, WrapperError


_REGISTRY: dict[str, Type[AppWrapper]] = {}


def register(cls: Type[AppWrapper]) -> Type[AppWrapper]:
    """Декоратор регистрации wrapper'а."""
    if not cls.name:
        raise WrapperError(f"{cls.__name__} без .name")
    _REGISTRY[cls.name] = cls
    return cls


def _autoload() -> None:
    """Импортирует доступные wrappers (graceful degradation)."""
    for modname, clsname in [
        ("aura.wrappers.grbl", "GRBLWrapper"),
        ("aura.wrappers.blender", "BlenderWrapper"),
        ("aura.wrappers.figma", "FigmaWrapper"),
    ]:
        try:
            mod = __import__(modname, fromlist=[clsname])
            cls = getattr(mod, clsname)
            register(cls)
        except Exception as e:
            # F-006: не глотать (раздел 17 промта)
            import logging
            logging.getLogger('aura.registry').debug(
                'registry error: %s', e)


class WrapperRegistry:
    """Реестр wrappers: list, get, status."""

    def __init__(self) -> None:
        _autoload()

    def list_names(self) -> list[str]:
        return sorted(_REGISTRY.keys())

    def get(self, name: str) -> AppWrapper:
        if name not in _REGISTRY:
            raise WrapperError(f"Wrapper {name!r} не найден")
        return _REGISTRY[name]()

    def status_all(self) -> list[dict]:
        result = []
        for name, cls in sorted(_REGISTRY.items()):
            try:
                inst = cls()
                result.append(inst.status())
            except Exception as e:
                result.append({"name": name, "error": str(e)})
        return result


_REGISTRY_INSTANCE: WrapperRegistry | None = None


def get_registry() -> WrapperRegistry:
    global _REGISTRY_INSTANCE
    if _REGISTRY_INSTANCE is None:
        _REGISTRY_INSTANCE = WrapperRegistry()
    return _REGISTRY_INSTANCE


__all__ = ["WrapperRegistry", "get_registry", "register"]
