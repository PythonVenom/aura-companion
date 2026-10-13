"""T016 — Notifications P0-P3.

Уровни (по важности):
  P0 — критично (SOS, падение, тревога)
  P1 — важно (медицина, батя, отказ агента)
  P2 — обычно (информация от агента)
  P3 — шум (отладка, heartbeat)

Маппинг priority int (legacy proactive.py, 7-95):
  >=90 → P0, >=70 → P1, >=40 → P2, иначе → P3

Почему notify-send: freedesktop-стандарт, работает в GNOME/KDE/XFCE,
не требует jeepney/dbus-python. Уровни -u: low/normal/critical.
"""
from __future__ import annotations

import enum
import shutil
import sqlite3
import subprocess
import time
from pathlib import Path

DB = Path.home() / ".local/share/aura/notifications.db"
APP_NAME = "Aura"


class NotifLevel(enum.IntEnum):
    P0 = 0  # критично
    P1 = 1  # важно
    P2 = 2  # обычно
    P3 = 3  # шум


_URGENCY = {
    NotifLevel.P0: "critical",
    NotifLevel.P1: "normal",
    NotifLevel.P2: "normal",
    NotifLevel.P3: "low",
}


def from_priority(priority: int) -> NotifLevel:
    """Legacy-маппинг: priority int → NotifLevel."""
    if priority >= 90:
        return NotifLevel.P0
    if priority >= 70:
        return NotifLevel.P1
    if priority >= 40:
        return NotifLevel.P2
    return NotifLevel.P3


def _ensure_db() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            level INTEGER NOT NULL,
            agent TEXT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            delivered INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def _log(level: NotifLevel, agent: str | None, title: str, body: str, delivered: bool) -> None:
    try:
        _ensure_db()
        conn = sqlite3.connect(DB)
        conn.execute(
            "INSERT INTO history (ts, level, agent, title, body, delivered) VALUES (?, ?, ?, ?, ?, ?)",
            (time.time(), int(level), agent, title, body, int(delivered)),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # никогда не падаем из-за логирования


def notify(level: NotifLevel, title: str, body: str, agent: str | None = None) -> bool:
    """Показать уведомление. True если доставлено."""
    urgency = _URGENCY[level]
    delivered = False
    if shutil.which("notify-send"):
        try:
            subprocess.run(
                ["notify-send", "-a", APP_NAME, "-u", urgency, title, body],
                check=False, timeout=2,
            )
            delivered = True
        except Exception:
            delivered = False
    _log(level, agent, title, body, delivered)
    return delivered


__all__ = ["NotifLevel", "notify", "from_priority"]
