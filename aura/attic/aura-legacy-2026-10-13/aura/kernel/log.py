"""Aura Event Log — источник истины.
Append-only JSONL. Immutable. Воспроизводимо.
Наука: Event Sourcing (Fowler 2005).
"""
import contextlib
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("aura.log")

LOG_DIR = Path.home() / ".local/share/aura/log"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class EventLog:
    def __init__(self, log_dir: Path = LOG_DIR):
        self.log_dir = log_dir
        self._fh = None
        self._day = None
        self._lock = threading.Lock()

    def _file_for_today(self) -> Path:
        return self.log_dir / f"{time.strftime('%Y-%m-%d')}.jsonl"

    def _ensure_open(self):
        today = time.strftime('%Y-%m-%d')
        if self._day != today:
            if self._fh:
                self._fh.close()
            path = self.log_dir / f"{today}.jsonl"
            self._fh = open(path, "a", encoding="utf-8")
            self._day = today

    def append(self, topic: str, payload: dict[str, Any],
               src: str = "", version: int = 1):
        """AURA_LOG_THREADSAFE_V1: Lock для многопоточности."""
        with self._lock:
            try:
                self._ensure_open()
                event = {
                    "ts": time.time(),
                    "topic": topic,
                    "v": version,
                    "src": src,
                    "payload": payload,
                }
                self._fh.write(json.dumps(event, ensure_ascii=False) + "\n")
                self._fh.flush()
            except Exception as e:
                # AURA_LOG_SILENT_V1: не роняем поток из-за лога
                print(f"[log] append failed: {e}")

    def tail(self, n: int = 20) -> list:
        path = self._file_for_today()
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        return [json.loads(l) for l in lines[-n:]]

    def close(self):
        """AURA_LOG_KEEP_OPEN_V1: не закрываем file — только flush.
        Worker threads могут ещё писать при shutdown.
        """
        with self._lock:
            if self._fh:
                with contextlib.suppress(Exception):
                    self._fh.flush()
                # File НЕ закрываем — пусть GC сделает
                self._fh = None


event_log = EventLog()
