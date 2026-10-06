"""T-eng-6 — Emergency stop (kill switch).

Наука:
- SCRAM (NRC 1979) — Nuclear reactor emergency shutdown
- Dead man's switch (Railroad 1880) — остановка при потере контроля
- ISO 13850 — Machinery emergency stop
- IEC 61508 — Functional safety (SIL)
- POSIX 1003.1 — signal handling

Идея: одна команда (голос, файл, сигнал, HTTP) — мгновенно
останавливает всё. Процессы, БД, соединения.
"""
from __future__ import annotations

import atexit
import signal
import sys
import threading
import time
from pathlib import Path
import contextlib

STOP_FILE = Path.home() / ".local/share/aura/STOP"
STATE_DIR = Path.home() / ".local/share/aura"

_stopped = False
_callbacks: list = []
_lock = threading.Lock()


def _ensure() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def is_stopped() -> bool:
    """Глобальный флаг — проверять в горячих циклах."""
    return _stopped or STOP_FILE.exists()


def register(callback) -> None:
    """Зарегистрировать callback — вызовется при stop()."""
    with _lock:
        _callbacks.append(callback)


def stop(reason: str = "", *, save_flag: bool = True) -> dict:
    """SCRAM — Emergency shutdown.

    Вызывает все зарегистрированные callbacks, пишет STOP-файл.
    Идемпотентно: второй вызов — без эффекта.
    """
    global _stopped
    with _lock:
        if _stopped:
            return {"already": True, "reason": reason}
        _stopped = True
        callbacks = list(_callbacks)

    results = []
    for cb in callbacks:
        try:
            cb()
            results.append({"callback": getattr(cb, "__name__", str(cb)),
                            "ok": True})
        except Exception as e:
            results.append({"callback": getattr(cb, "__name__", str(cb)),
                            "ok": False, "error": str(e)[:100]})

    if save_flag:
        _ensure()
        try:
            STOP_FILE.write_text(
                f"{time.time()}\n{reason}\n",
                encoding="utf-8",
            )
        except Exception as e:
            # F-006: если STOP_FILE не записан — система НЕ остановится
            # при следующем рестарте. Это критично — не глотать.
            import logging
            logging.getLogger("aura.emergency").critical(
                "STOP_FILE write failed: %s — stop flag NOT persisted",
                e, exc_info=True)

    return {
        "stopped": True,
        "reason": reason,
        "callbacks_called": len(callbacks),
        "results": results,
    }


def resume() -> bool:
    """Снять STOP-флаг. Ручной restart."""
    global _stopped
    with _lock:
        _stopped = False
    if STOP_FILE.exists():
        STOP_FILE.unlink()
    return True


def install_signal_handlers() -> None:
    """POSIX signals → stop().

    SIGINT  (Ctrl+C)  — soft stop
    SIGTERM (kill)    — soft stop
    SIGUSR1 (custom)  — emergency stop
    """
    def _handler(signum, frame):
        sig_name = signal.Signals(signum).name
        stop(f"signal {sig_name}")
        sys.exit(130 if signum == signal.SIGINT else 0)

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGUSR1):
        with contextlib.suppress(ValueError, OSError):
            signal.signal(sig, _handler)


def check_and_raise() -> None:
    """Публичный API для hot loops: если STOP — raise SystemExit.

    Использование:
        for msg in stream:
            emergency_stop.check_and_raise()
            process(msg)
    """
    if is_stopped():
        raise SystemExit("Aura stopped (STOP flag)")


def watch_trigger_file(poll_sec: float = 1.0) -> threading.Thread:
    """Фоновый поток: если STOP-файл появился — вызвать stop().

    Позволяет внешнему процессу остановить Aura через `touch STOP`.
    """
    def _watch():
        while not _stopped:
            if STOP_FILE.exists():
                stop("STOP file detected")
                return
            time.sleep(poll_sec)

    t = threading.Thread(target=_watch, daemon=True)
    t.start()
    return t


def status() -> dict:
    """Публичный API: состояние."""
    return {
        "stopped": is_stopped(),
        "stop_file_exists": STOP_FILE.exists(),
        "callbacks_registered": len(_callbacks),
    }


@atexit.register
def _on_exit() -> None:
    """Гарантированный stop при выходе процесса."""
    global _stopped
    _stopped = True


__all__ = [
    "STOP_FILE",
    "check_and_raise",
    "install_signal_handlers",
    "is_stopped",
    "register",
    "resume",
    "status",
    "stop",
    "watch_trigger_file",
]
