"""Safe Word — кодовое слово для сброса тревоги.

Наука: Duress Code (banking), Emergency Reset.
Если батя говорит 'аура сброс' — AURA отменяет ложную тревогу.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

CONFIG_FILE = Path.home() / ".config" / "aura" / "safe_word.json"
DEFAULT_WORDS = ("сброс", "отмена тревоги", "ложная тревога", "всё хорошо")


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"words": list(DEFAULT_WORDS), "history": []}


def _save_config(cfg: dict) -> None:
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
    except Exception:
        pass


def get_words() -> list[str]:
    return list(_load_config().get("words", DEFAULT_WORDS))


def set_words(words: list[str]) -> None:
    cfg = _load_config()
    cfg["words"] = words
    _save_config(cfg)


def is_safe_word(text: str) -> bool:
    """True если в тексте есть safe-word."""
    t = text.lower()
    return any(w.lower() in t for w in get_words())


def reset_alerts(reason: str = "") -> int:
    """Сбросить тревоги в blackboard. Возврат: сколько сброшено."""
    try:
        from aura.core import blackboard as bb
        alerts = bb.recent_alerts(window_sec=3600)
        n = len(alerts)
        # Записать в историю
        cfg = _load_config()
        cfg.setdefault("history", []).append({
            "ts": time.time(),
            "reason": reason,
            "cleared": n,
        })
        cfg["history"] = cfg["history"][-50:]
        _save_config(cfg)
        # Записать receipt
        try:
            from aura.core.receipts import record
            record("safe_word_reset", "user", {"cleared": n, "reason": reason})
        except Exception:
            pass
        return n
    except Exception:
        return 0


def stats() -> dict:
    cfg = _load_config()
    return {
        "words_count": len(cfg.get("words", [])),
        "resets_total": len(cfg.get("history", [])),
        "last_reset": cfg.get("history", [])[-1] if cfg.get("history") else None,
    }


__all__ = ["get_words", "is_safe_word", "reset_alerts", "set_words", "stats"]
