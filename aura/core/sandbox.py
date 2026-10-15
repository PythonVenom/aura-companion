"""Sandbox — изоляция пользователей AURA (multi-tenant).

Наука: AgentOS (openJiuwen), tenant isolation.
Каждый пользователь — отдельный sandbox с своими:
- blackboard
- memory hub
- affinity
- settings
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

DEFAULT_TENANT = "default"


class Tenant:
    """Изолированный пользователь AURA."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.root = Path.home() / ".local" / "share" / "aura" / "tenants" / name
        self.root.mkdir(parents=True, exist_ok=True)
        self._setup_env()

    def _setup_env(self) -> None:
        """Переключить окружение на sandbox."""
        os.environ["AURA_TENANT"] = self.name
        os.environ["XDG_CACHE_HOME"] = str(self.root / "cache")
        os.environ["XDG_CONFIG_HOME"] = str(self.root / "config")
        os.environ["XDG_DATA_HOME"] = str(self.root / "data")

    @property
    def blackboard_path(self) -> Path:
        return self.root / "cache" / "aura" / "blackboard.json"

    @property
    def affinity_path(self) -> Path:
        return self.root / "cache" / "aura" / "affinity.json"

    @property
    def memory_db(self) -> Path:
        return self.root / "data" / "aura" / "recall.db"

    def reset(self) -> None:
        """Очистить sandbox."""
        shutil.rmtree(self.root, ignore_errors=True)
        self.root.mkdir(parents=True, exist_ok=True)


def current_tenant() -> str:
    return os.environ.get("AURA_TENANT", DEFAULT_TENANT)


def list_tenants() -> list[str]:
    root = Path.home() / ".local" / "share" / "aura" / "tenants"
    if not root.exists():
        return [DEFAULT_TENANT]
    out = [DEFAULT_TENANT]
    for d in root.iterdir():
        if d.is_dir() and d.name != DEFAULT_TENANT:
            out.append(d.name)
    return out


def switch(name: str) -> Tenant:
    """Переключиться на tenant."""
    return Tenant(name)


__all__ = ["DEFAULT_TENANT", "Tenant", "current_tenant", "list_tenants", "switch"]
