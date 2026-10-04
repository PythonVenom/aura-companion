"""
Watchdog: следит, что главный цикл Ауры не завис.

Раз в CHECK_INTERVAL_SEC секунд проверяет timestamp последнего
вызова beat(). Если цикл не обновлялся MAX_STALE_SEC секунд —
os._exit(1). Systemd (Restart=on-failure) поднимает Ауру.

Зачем: если listener.listen() заблокируется навсегда, или LLM
зависнет — Аура тихо умрёт. Watchdog её поднимет.

Почему не sd_notify: не требует systemd-python или sdnotify,
не требует Type=notify в unit. Работает с Type=simple.
"""

from __future__ import annotations

import os
import threading
import time


CHECK_INTERVAL_SEC = 30     # как часто проверяем
MAX_STALE_SEC = 180         # сколько тишины до рестарта


class Heartbeat:
    """Простой watchdog на daemon-thread."""

    def __init__(self, on_stale=None):
        self._last = time.time()
        self._running = False
        self._thread = None
        self._on_stale = on_stale or self._default_exit

    def beat(self) -> None:
        """Обновить timestamp. Звать в главном цикле."""
        self._last = time.time()

    def start(self) -> bool:
        """Запустить watchdog. True если запущен."""
        if self._running:
            return True
        self._last = time.time()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._running = False

    @staticmethod
    def _default_exit() -> None:
        print(
            f"💀 Heartbeat: цикл не обновлялся {MAX_STALE_SEC}с — "
            f"выход для перезапуска systemd",
            flush=True,
        )
        os._exit(1)

    def _loop(self) -> None:
        while self._running:
            time.sleep(CHECK_INTERVAL_SEC)
            if not self._running:
                break
            stale = time.time() - self._last
            if stale > MAX_STALE_SEC:
                try:
                    self._on_stale()
                except Exception:
                    pass
                return


__all__ = ["Heartbeat", "CHECK_INTERVAL_SEC", "MAX_STALE_SEC"]

