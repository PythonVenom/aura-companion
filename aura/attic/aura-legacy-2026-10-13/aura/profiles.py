"""Profiles — управление профилями Aura.

Один код — много профилей. Каждый профиль имеет:
- свою state.db (память)
- свой modules.toml (какие агенты включены)
- свой config.toml (настройки)
- свой STORY.md (журнал)

Наука: Saltzer & Schroeder 1975 (least privilege),
       Brooks 1975 (база > фичи).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO = Path("/home/pythonvenom/aura_project")
PROFILES_DIR = REPO / "profiles"
DEFAULT_PROFILE = "captain"


@dataclass
class Profile:
    """Один профиль Aura."""

    name: str
    path: Path

    @property
    def state_db(self) -> Path:
        return self.path / "state.db"

    @property
    def config(self) -> Path:
        return self.path / "config.toml"

    @property
    def modules(self) -> Path:
        return self.path / "modules.toml"

    @property
    def story(self) -> Path:
        return self.path / "STORY.md"

    def exists(self) -> bool:
        return self.path.exists()


def current_profile() -> str:
    """Текущий профиль.

    Приоритет:
      1. env AURA_PROFILE
      2. файл ~/.config/aura/profile
      3. DEFAULT_PROFILE (captain)
    """
    env = os.environ.get("AURA_PROFILE")
    if env:
        return env
    marker = Path.home() / ".config" / "aura" / "profile"
    if marker.exists():
        try:
            name = marker.read_text(encoding="utf-8").strip()
            if name:
                return name
        except Exception:
            pass
    return DEFAULT_PROFILE


def get_profile(name: str | None = None) -> Profile:
    """Получить профиль по имени (или текущий)."""
    name = name or current_profile()
    path = PROFILES_DIR / name
    path.mkdir(parents=True, exist_ok=True)
    return Profile(name=name, path=path)


def switch_profile(name: str) -> None:
    """Переключить глобальный профиль."""
    marker = Path.home() / ".config" / "aura" / "profile"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(name, encoding="utf-8")


def list_profiles() -> list[str]:
    """Список существующих профилей."""
    if not PROFILES_DIR.exists():
        return []
    return sorted(
        p.name for p in PROFILES_DIR.iterdir()
        if p.is_dir() and not p.name.startswith("_")
    )


def ensure_profile(name: str, template: str = "captain") -> Profile:
    """Создать профиль если нет, копируя шаблон."""
    profile = get_profile(name)
    if profile.exists() and profile.state_db.exists():
        return profile

    # Копируем из шаблона
    template_path = PROFILES_DIR / template
    if template_path.exists() and template_path != profile.path:
        import shutil
        for item in template_path.iterdir():
            if item.is_file():
                shutil.copy2(item, profile.path / item.name)

    return profile


__all__ = [
    "DEFAULT_PROFILE",
    "PROFILES_DIR",
    "Profile",
    "current_profile",
    "ensure_profile",
    "get_profile",
    "list_profiles",
    "switch_profile",
]
