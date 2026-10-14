"""#156 API Versioning — SemVer для агентов и API.

Наука:
- SemVer 2.0 (Preston-Werner 2013) — MAJOR.MINOR.PATCH
- Fielding 2000 (REST) — API versioning для эволюции
- Hyrum's Law (Wright 2015) — «все наблюдаемые поведения становятся API»

Зачем:
  Когда агенты/плагины зависят от API — их надо предупреждать о breaking changes.
  Декоратор @api("1.2.0") + реестр совместимости.
"""
from __future__ import annotations

import functools
import re
from dataclasses import dataclass

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-([\w.]+))?$")


@dataclass(frozen=True)
class APIVersion:
    major: int
    minor: int
    patch: int
    prerelease: str = ""

    @classmethod
    def parse(cls, s: str) -> "APIVersion":
        m = SEMVER_RE.match(s)
        if not m:
            raise ValueError(f"Invalid SemVer: {s}")
        return cls(int(m.group(1)), int(m.group(2)),
                   int(m.group(3)), m.group(4) or "")

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        return f"{base}-{self.prerelease}" if self.prerelease else base

    def is_compatible(self, other: "APIVersion") -> bool:
        """Совместим ли other с self (same MAJOR)."""
        return self.major == other.major


# Текущая версия API (меняется вручную при breaking change)
CURRENT_API = APIVersion.parse("1.0.0")

# Реестр зарегистрированных агентов/функций
_REGISTRY: dict[str, APIVersion] = {}


def api(version: str):
    """Декоратор: помечает функцию/класс версией API."""
    v = APIVersion.parse(version)

    def deco(obj):
        name = getattr(obj, "__name__", str(obj))
        _REGISTRY[name] = v
        obj.__api_version__ = v
        return obj
    return deco


def registered() -> dict[str, str]:
    """Список зарегистрированных с версиями."""
    return {k: str(v) for k, v in _REGISTRY.items()}


def is_compatible(version: str) -> bool:
    """Совместима ли версия с текущей API."""
    try:
        v = APIVersion.parse(version)
    except ValueError:
        return False
    return CURRENT_API.is_compatible(v)


def check_all() -> list[str]:
    """Проверить все зарегистрированные. Возвращает несовместимые."""
    bad = []
    for name, v in _REGISTRY.items():
        if not CURRENT_API.is_compatible(v):
            bad.append(f"{name}@{v}")
    return bad


__all__ = [
    "APIVersion", "CURRENT_API", "api", "registered",
    "is_compatible", "check_all",
]
