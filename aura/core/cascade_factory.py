"""Factory для Resolution Cascade в конкретных агентах (ADR-098)."""
from __future__ import annotations

import shutil
import subprocess

from aura.core.resolver import make_cascade

APP_MAP = {
    "vscode": "code", "код": "code",
    "firefox": "firefox", "фаерфокс": "firefox",
    "brave": "brave", "chromium": "chromium",
    "terminal": "konsole", "терминал": "konsole",
    "konsole": "konsole", "dolphin": "dolphin",
    "telegram": "telegram-desktop",
}


def resolve_app(target: str, ctx: dict) -> str | None:
    name = APP_MAP.get(target.lower())
    if not name:
        return None
    path = shutil.which(name)
    return path


def resolve_window(target: str, ctx: dict) -> str | None:
    try:
        r = subprocess.run(
            ["wmctrl", "-l"], capture_output=True, text=True, timeout=2,
        )
        for line in r.stdout.splitlines():
            if target.lower() in line.lower():
                return line
    except Exception as e:
        # F-006: не глотать (раздел 17 промта)
        import logging
        logging.getLogger('aura.cascade_factory').warning(
            'cascade_factory error: %s', e)
    return None


def build_app_cascade():
    return make_cascade(
        app_resolver=resolve_app,
        window_resolver=resolve_window,
    )


__all__ = ["APP_MAP", "build_app_cascade", "resolve_app", "resolve_window"]
