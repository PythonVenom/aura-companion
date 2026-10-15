"""Индикаторы статуса AURA (сеть, агенты, речь, офлайн).

Наука: WCAG 2.2 (visible status, keyboard access).
Формат: emoji + краткий текст.
"""
from __future__ import annotations

import socket
from pathlib import Path


def is_online() -> bool:
    """Проверить интернет (ping 8.8.8.8:53)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect(("8.8.8.8", 53))
        s.close()
        return True
    except Exception:
        return False


def is_silent() -> bool:
    """Режим тишины?"""
    return (Path.home() / ".cache" / "aura" / "silent_mode").exists()


def status_line() -> str:
    """Одна строка статуса: 🟢 онлайн | 🤖 110 агентов | 🔊 звук."""
    net = "🟢 онлайн" if is_online() else "⚫ офлайн"
    voice = "🔇 тишина" if is_silent() else "🔊 звук"
    try:
        from aura.core import blackboard as bb
        snap = bb.snapshot()
        sector = snap.get("sector", "unknown")
        alerts = len(bb.recent_alerts(window_sec=300))
        alert_mark = f"⚠️ {alerts}" if alerts else "✅"
        return f"{net} | 🤖 сектор: {sector} | {alert_mark} | {voice}"
    except Exception:
        return f"{net} | 🤖 AURA | {voice}"


def full_status() -> str:
    """Полный статус для boot-report."""
    lines = [status_line()]
    try:
        from aura.bootstrap import build_orchestrator
        n = len(build_orchestrator())
        lines.append(f"  Агентов: {n}")
    except Exception:
        pass
    return "\n".join(lines)


__all__ = ["is_online", "is_silent", "status_line", "full_status"]


if __name__ == "__main__":
    print(full_status())
