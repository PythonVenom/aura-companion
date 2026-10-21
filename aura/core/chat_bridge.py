"""ChatBridge — file-based IPC для чата с Aura.

ADR-069: QML widget пишет в chat_inbox.jsonl, ChatBridge читает,
aura_main обрабатывает через orchestrator, результат → chat_history.jsonl.

Почему файлы, не DBus:
- python-dbus в venv не стоит
- Тот же паттерн что aura/status.py (проверен)
- Тестируется в pytest без mock
- Graceful degradation: Aura упала → inbox копится
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

DEFAULT_CACHE = Path(os.environ.get(
    "AURA_CACHE_DIR",
    str(Path.home() / ".cache/aura"),
))


class ChatBridge:
    def __init__(self, inbox_path=None, history_path=None):
        self.inbox_path = (
            Path(inbox_path) if inbox_path else DEFAULT_CACHE / "chat_inbox.jsonl"
        )
        self.history_path = (
            Path(history_path) if history_path else DEFAULT_CACHE / "chat_history.jsonl"
        )
        self._offset = 0
        self._inode = 0
        if self.inbox_path.exists():
            st = self.inbox_path.stat()
            self._offset = st.st_size
            self._inode = st.st_ino
        self._inode = self.inbox_path.stat().st_ino

    def read_new(self) -> list[dict]:
        """Всегда читает весь INBOX. Дедупликация — в _drain_chat_queue."""
        if not self.inbox_path.exists():
            return []
        msgs = []
        try:
            with open(self.inbox_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msgs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except Exception:
            return []
        return msgs

    def append_history(self, user: str, aura: str) -> None:
        """Дописать пару user/aura в history (атомарный append)."""
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        _ts = time.time()
        from datetime import datetime as _dt
        _now = _dt.fromtimestamp(_ts)
        payload = {
            "user": user or "",
            "aura": aura or "",
            "ts": _ts,
            "date": _now.strftime("%Y-%m-%d"),
            "time": _now.strftime("%H:%M:%S"),
            "session": getattr(self, "_session_id", "default"),
        }
        try:
            with open(self.history_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            # F-006: не глотать (раздел 17 промта)
            import logging
            logging.getLogger('aura.chat_bridge').warning(
                'chat_bridge error: %s', e)


__all__ = ["DEFAULT_CACHE", "ChatBridge"]
