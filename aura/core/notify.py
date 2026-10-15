"""Notify — системные уведомления AURA.

Наука: Desktop Notifications Spec (freedesktop.org).
Fallback: если notify-send нет — лог в файл.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

LOG_FILE = Path.home() / ".cache" / "aura" / "notifications.log"


def _has_notify_send() -> bool:
    return shutil.which("notify-send") is not None


def notify(title: str, body: str, urgency: str = "normal") -> bool:
    """Отправить уведомление.

    urgency: low | normal | critical
    """
    if _has_notify_send():
        try:
            subprocess.run(
                ["notify-send", "-u", urgency, "-a", "AURA", title, body],
                check=False, timeout=5,
            )
            return True
        except Exception:
            pass
    # Fallback: лог
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{urgency}] {title}: {body}\n")
        return True
    except Exception:
        return False


def critical(title: str, body: str) -> bool:
    """Критичное уведомление (не исчезает)."""
    return notify(title, body, urgency="critical")


def info(title: str, body: str) -> bool:
    return notify(title, body, urgency="normal")


__all__ = ["critical", "info", "notify"]
