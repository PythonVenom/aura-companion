#!/usr/bin/env python3
"""Push-to-stop: watcher файла /tmp/aura.stop.

KDE hotkey Meta+Shift+S → touch /tmp/aura.stop.
Aura видит файл → stop_speaking().
Работает без AEC — не зависит от WirePlumber.

См. ADR-009 (AEC) + ADR-050 (push-to-stop fallback).
"""
from __future__ import annotations
import time
from pathlib import Path

STOP_FILE = Path("/tmp/aura.stop")
CHECK_INTERVAL = 0.1


def watch(speaker, on_stop=None) -> None:
    """Блокирующий цикл. Вызывать в daemon-thread."""
    while True:
        try:
            if STOP_FILE.exists():
                STOP_FILE.unlink(missing_ok=True)
                try:
                    speaker.stop_speaking()
                    print("⏹ Push-to-stop: остановила речь", flush=True)
                except Exception as e:
                    print(f"⚠ Push-to-stop error: {e}", flush=True)
                if on_stop is not None:
                    try:
                        on_stop()
                    except Exception as e:
                        print(f"⚠ on_stop callback: {e}", flush=True)
        except Exception as e:
            print(f"⚠ watcher loop: {e}", flush=True)
        time.sleep(CHECK_INTERVAL)


__all__ = ["watch", "STOP_FILE"]
