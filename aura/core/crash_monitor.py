"""T081 — Crash monitor + heartbeat.

Наука:
- Watchdog (Linux kernel docs) — обнаружение зависаний
- Heartbeat (Tanenbaum, «Distributed Systems»)
- Crash reporting (Mozilla Socorro 2007) — сбор падений
- Structured logging (Majors 2015) — JSON для анализа
- MTBF (IEEE 1997) — метрика «0 крашей за 30 дней»

Цель: доказать, что Aura стабильна 30+ дней подряд.
Пишем heartbeat раз в 5 мин, crash при исключении.
"""
from __future__ import annotations

import json
import os
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path

STATE_DIR = Path.home() / ".local/share/aura/stability"
HEARTBEAT_FILE = STATE_DIR / "heartbeat.json"
CRASH_LOG = STATE_DIR / "crashes.jsonl"
START_FILE = STATE_DIR / "started_at.txt"

HEARTBEAT_INTERVAL_SEC = 300  # 5 минут
STABILITY_WINDOW_DAYS = 30


def _ensure() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def mark_start() -> None:
    """Отметить старт процесса. Первый запуск = начало наблюдения."""
    _ensure()
    if not START_FILE.exists():
        START_FILE.write_text(str(time.time()), encoding="utf-8")
    _write_heartbeat()


def _write_heartbeat() -> None:
    _ensure()
    hb = {
        "pid": os.getpid(),
        "ts": time.time(),
        "iso": datetime.now(UTC).isoformat(),
        "uptime_sec": time.time() - float(START_FILE.read_text().strip() or 0),
    }
    HEARTBEAT_FILE.write_text(
        json.dumps(hb, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def heartbeat() -> None:
    """Публичный API: вызвать раз в 5 мин."""
    _write_heartbeat()


def record_crash(exc: BaseException, context: str = "") -> None:
    """Публичный API: записать падение в журнал."""
    _ensure()
    entry = {
        "ts": time.time(),
        "iso": datetime.now(UTC).isoformat(),
        "type": type(exc).__name__,
        "message": str(exc)[:500],
        "context": context[:200],
        "traceback": traceback.format_exc()[-2000:],
        "pid": os.getpid(),
    }
    with CRASH_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def install_excepthook() -> None:
    """Публичный API: перехватывать все необработанные исключения."""
    import sys

    def _hook(exc_type, exc, tb):
        record_crash(exc, context="excepthook")
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _hook


# --- Метрики ---

def uptime_days() -> float:
    """Дней с первого запуска."""
    if not START_FILE.exists():
        return 0.0
    started = float(START_FILE.read_text().strip() or 0)
    return (time.time() - started) / 86400.0


def last_heartbeat_age_sec() -> float:
    """Секунд с последнего heartbeat. Больше 600 = зависание."""
    if not HEARTBEAT_FILE.exists():
        return float("inf")
    try:
        hb = json.loads(HEARTBEAT_FILE.read_text(encoding="utf-8"))
        return time.time() - float(hb["ts"])
    except Exception:
        return float("inf")


def crash_count(since_days: int = STABILITY_WINDOW_DAYS) -> int:
    """Число падений за N дней."""
    if not CRASH_LOG.exists():
        return 0
    since = time.time() - since_days * 86400
    n = 0
    for line in CRASH_LOG.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
            if entry.get("ts", 0) >= since:
                n += 1
        except Exception:
            continue
    return n


def mtbf_days() -> float:
    """Mean Time Between Failures — дней между падениями. inf = ни одного."""
    c = crash_count()
    if c == 0:
        return float("inf")
    return uptime_days() / c


def stability_report() -> dict:
    """Публичный API: полный отчёт стабильности."""
    return {
        "uptime_days": round(uptime_days(), 2),
        "last_heartbeat_age_sec": round(last_heartbeat_age_sec(), 1),
        "crashes_30d": crash_count(30),
        "crashes_all_time": crash_count(36500),
        "mtbf_days": mtbf_days() if mtbf_days() != float("inf") else None,
        "target": {
            "uptime_days": STABILITY_WINDOW_DAYS,
            "crashes": 0,
            "healthy": crash_count(30) == 0 and uptime_days() >= STABILITY_WINDOW_DAYS,
        },
    }


def reset() -> None:
    """Публичный API: сбросить наблюдение (осторожно!)."""
    for f in (HEARTBEAT_FILE, CRASH_LOG, START_FILE):
        if f.exists():
            f.unlink()


__all__ = [
    "crash_count",
    "heartbeat",
    "install_excepthook",
    "last_heartbeat_age_sec",
    "mark_start",
    "mtbf_days",
    "record_crash",
    "reset",
    "stability_report",
    "uptime_days",
]
