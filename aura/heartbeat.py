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

import logging
import os
import threading
import time

log = logging.getLogger("aura.heartbeat")


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
                except Exception as e:
                    # F-006: не глотаем, но и не крэшим процесс.
                    # Контракт (test_callback_exception_does_not_crash):
                    # callback — best-effort. Упал → логируем.
                    # Watchdog сам Aura не убивает — это работа systemd.
                    log.critical("Heartbeat._on_stale() failed: %s", e,
                                 exc_info=True)
                return


__all__ = ["CHECK_INTERVAL_SEC", "MAX_STALE_SEC", "Heartbeat"]

