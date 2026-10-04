"""Единый логгер Ауры с уровнями.

Использование:
    from aura.logger import info, warn, error
    info("Загружено агентов", count=27)
    error("Ошибка T-one", exc=e)
"""
from __future__ import annotations

import sys
import time


LEVELS = {"debug": 0, "info": 1, "warn": 2, "error": 3}
_CURRENT = "info"


def set_level(level: str) -> None:
    global _CURRENT
    if level in LEVELS:
        _CURRENT = level


def _log(level: str, msg: str, **kw) -> None:
    if LEVELS[level] < LEVELS[_CURRENT]:
        return
    prefix = {"debug": "🔍", "info": "ℹ️", "warn": "⚠️", "error": "❌"}[level]
    extras = " ".join(f"{k}={v}" for k, v in kw.items())
    line = f"{prefix} [{level}] {msg}"
    if extras:
        line += f" | {extras}"
    print(line, file=sys.stderr if level == "error" else sys.stdout, flush=True)


def debug(msg: str, **kw) -> None: _log("debug", msg, **kw)
def info(msg: str, **kw) -> None: _log("info", msg, **kw)
def warn(msg: str, **kw) -> None: _log("warn", msg, **kw)
def error(msg: str, **kw) -> None: _log("error", msg, **kw)


__all__ = ["set_level", "debug", "info", "warn", "error", "LEVELS"]
