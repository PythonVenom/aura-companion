"""Focus — «не отвлекать N минут» (ADR-097)."""
from __future__ import annotations
import time
from pathlib import Path


FLAG = Path("/tmp/aura_focus")
DEFAULT_TIMEOUT = 3600


def enable(seconds: int = DEFAULT_TIMEOUT) -> None:
    FLAG.write_text(str(time.time() + seconds), encoding="utf-8")


def disable() -> None:
    FLAG.unlink(missing_ok=True)


def is_active() -> bool:
    if not FLAG.exists():
        return False
    try:
        until = float(FLAG.read_text(encoding="utf-8").strip())
    except Exception:
        FLAG.unlink(missing_ok=True)
        return False
    if time.time() > until:
        FLAG.unlink(missing_ok=True)
        return False
    return True


def remaining() -> float:
    if not is_active():
        return 0.0
    try:
        until = float(FLAG.read_text(encoding="utf-8").strip())
    except Exception:
        return 0.0
    return max(0.0, until - time.time())


__all__ = ["enable", "disable", "is_active", "remaining", "FLAG", "DEFAULT_TIMEOUT"]
