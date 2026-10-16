"""ChatWatcher — thread, читает inbox → queue.

ADR-069: main loop забирает сообщения из queue, обрабатывает через
orchestrator, пишет в history. Watcher — только I/O, ноль логики.

Паттерн скопирован с aura_stop_watcher.py (push-to-stop).
"""
from __future__ import annotations

import queue
import threading
import time


class ChatWatcher(threading.Thread):
    def __init__(self, bridge, msg_queue: queue.Queue, interval: float = 0.3):
        super().__init__(daemon=True, name="aura-chat")
        self.bridge = bridge
        self.queue = msg_queue
        self.interval = interval
        self._stop_event = threading.Event()

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                for msg in self.bridge.read_new():
                    self.queue.put(msg)
            except Exception as e:
                print(f"⚠️ ChatWatcher: {e}", flush=True)
            time.sleep(self.interval)

    def stop(self) -> None:
        self._stop_event.set()


__all__ = ["ChatWatcher"]
