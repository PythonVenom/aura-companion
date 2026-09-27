"""Bug 14: помним последний активный медиа-источник.

«включи/продолжи/пауза» без явного источника → тот же плеер.
TTL 30 мин — не помним вечно.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

STATE_PATH = Path("/tmp/aura_media_state.json")
_TTL = 1800.0   # 30 мин

VALID = frozenset({"vk", "local", "mpris"})


def set_active(source: str, chat: str = "") -> None:
    """Запомнить активный источник."""
    if source not in VALID:
        return
    try:
        STATE_PATH.write_text(
            json.dumps({"source": source, "chat": chat, "ts": time.time()},
                       ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


def get_active() -> str | None:
    """Вернуть source или None если пусто/протухло."""
    try:
        if not STATE_PATH.exists():
            return None
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        ts = data.get("ts", 0)
        if time.time() - ts > _TTL:
            return None
        s = data.get("source", "")
        return s if s in VALID else None
    except Exception:
        return None


def get_active_chat() -> str:
    try:
        if not STATE_PATH.exists():
            return ""
        return json.loads(STATE_PATH.read_text(encoding="utf-8")).get("chat", "")
    except Exception:
        return ""


def clear() -> None:
    try:
        STATE_PATH.unlink(missing_ok=True)
    except Exception:
        pass


__all__ = ["set_active", "get_active", "get_active_chat", "clear", "STATE_PATH"]
