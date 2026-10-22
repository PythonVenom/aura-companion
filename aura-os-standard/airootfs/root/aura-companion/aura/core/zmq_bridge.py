"""ZeroMQ event bridge — межпроцессная шина событий.

Наука: ZeroMQ (Hintjens 2013), PUB/SUB pattern.
Назначение: масштабирование AURA на несколько процессов/машин.
Fallback: если pyzmq нет — работает через asyncio (no-op).
"""
from __future__ import annotations

import json
import threading
from typing import Any

zmq: Any = None
try:
    import zmq  # type: ignore[no-redef]
    HAS_ZMQ = True
except ImportError:
    HAS_ZMQ = False

DEFAULT_PUB = "tcp://127.0.0.1:5555"
DEFAULT_SUB = "tcp://127.0.0.1:5556"


class ZMQBridge:
    """PUB/SUB шина для событий AURA."""

    def __init__(self, pub_addr: str = DEFAULT_PUB) -> None:
        self.pub_addr = pub_addr
        self._ctx: Any = None
        self._pub: Any = None
        self._ready = False
        self._lock = threading.Lock()
        if HAS_ZMQ:
            try:
                self._ctx = zmq.Context()
                self._pub = self._ctx.socket(zmq.PUB)
                self._pub.bind(pub_addr)
                self._ready = True
            except Exception:
                self._ready = False

    @property
    def ready(self) -> bool:
        return self._ready

    def publish(self, topic: str, payload: dict[str, Any]) -> bool:
        """Отправить событие в шину."""
        if not self._ready or self._pub is None:
            return False
        try:
            with self._lock:
                msg = json.dumps(payload, ensure_ascii=False)
                self._pub.send_string(f"{topic} {msg}")
            return True
        except Exception:
            return False

    def close(self) -> None:
        if self._pub is not None:
            self._pub.close()
        if self._ctx is not None:
            self._ctx.term()


_BRIDGE: ZMQBridge | None = None


def get_bridge() -> ZMQBridge:
    global _BRIDGE
    if _BRIDGE is None:
        _BRIDGE = ZMQBridge()
    return _BRIDGE


__all__ = ["HAS_ZMQ", "ZMQBridge", "get_bridge"]
