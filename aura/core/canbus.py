"""#36 AgentCANBus — шина pub/sub для агентов Aura.

Наука:
- Event-Driven Architecture (Hohpe & Woolf 2003, "Enterprise Integration Patterns")
- Actor Model (Hewitt 1973) — изолированные акторы общаются сообщениями
- Reactive Manifesto (2014) — message-driven, resilient

Зачем:
  Сейчас агенты общаются через orchestrator (звезда). Это O(N) на маршрут.
  CANBus даёт O(1) — агент публикует в канал, подписчики получают.
  Позволяет: meds → sos (без orchestrator), fall → notify (параллельно).

Дизайн:
  Channel("meds.taken")    — иерархические имена
  publish(channel, msg)     — отправить
  subscribe(channel, cb)    — подписаться (с wildcard: "meds.*")
  Ring-buffer 1000 сообщений (защита от утечек)
  SQLite — offline-персистентность (опционально, TODO)

НЕ путать с:
- aura/core/dbus_service.py — D-Bus (внешняя IPC с GNOME/KDE)
- aura/core/dispatcher.py — маршрутизация LLM-запросов
"""
from __future__ import annotations

import re
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable

# Максимальный размер ring-buffer
HISTORY_SIZE = 1000


@dataclass
class Message:
    channel: str
    payload: Any
    sender: str
    ts: float = field(default_factory=time.time)


def _matches(pattern: str, channel: str) -> bool:
    """Wildcard-матч: 'meds.*' матчит 'meds.taken', но не 'meds.a.b'."""
    if pattern == channel:
        return True
    # "meds.*" → regex ^meds\.[^.]+$
    regex = "^" + re.escape(pattern).replace(r"\*", "[^.]+") + "$"
    return re.match(regex, channel) is not None


class AgentCANBus:
    """Шина сообщений между агентами."""

    def __init__(self, history_size: int = HISTORY_SIZE) -> None:
        # subscribers[channel_pattern] = [callbacks]
        self._subscribers: dict[str, list[Callable[[Message], None]]] = {}
        # Ring-buffer для аудита (защита от утечек)
        self._history: deque[Message] = deque(maxlen=history_size)
        # Счётчики для метрик
        self._stats: dict[str, int] = {"published": 0, "delivered": 0, "dropped": 0}

    # ─── Публикация ───
    def publish(self, channel: str, payload: Any, sender: str = "unknown") -> int:
        """Опубликовать сообщение. Возвращает число получателей."""
        if not channel:
            raise ValueError("channel не может быть пустым")
        msg = Message(channel=channel, payload=payload, sender=sender)
        self._history.append(msg)
        self._stats["published"] += 1

        delivered = 0
        for pattern, callbacks in self._subscribers.items():
            if _matches(pattern, channel):
                for cb in callbacks:
                    try:
                        cb(msg)
                        delivered += 1
                    except Exception:
                        self._stats["dropped"] += 1
        self._stats["delivered"] += delivered
        return delivered

    # ─── Подписка ───
    def subscribe(self, channel: str, callback: Callable[[Message], None]) -> None:
        """Подписаться на канал (поддерживает wildcard 'channel.*')."""
        if not channel:
            raise ValueError("channel не может быть пустым")
        if not callable(callback):
            raise TypeError("callback должен быть вызываемым")
        self._subscribers.setdefault(channel, []).append(callback)

    def unsubscribe(self, channel: str, callback: Callable[[Message], None]) -> bool:
        """Отписаться. True если найден и удалён."""
        if channel in self._subscribers:
            try:
                self._subscribers[channel].remove(callback)
                if not self._subscribers[channel]:
                    del self._subscribers[channel]
                return True
            except ValueError:
                return False
        return False

    # ─── Broadcast ───
    def broadcast(self, payload: Any, sender: str = "system") -> int:
        """Отослать всем подписчикам (специальный канал '*')."""
        return self.publish("*", payload, sender)

    # ─── История ───
    def history(self, channel: str | None = None, limit: int = 50) -> list[Message]:
        """Последние сообщения (по каналу или все)."""
        items = list(self._history)
        if channel is not None:
            items = [m for m in items if _matches(channel, m.channel)]
        return items[-limit:]

    # ─── Метрики ───
    def stats(self) -> dict:
        return {
            **self._stats,
            "channels": len(self._subscribers),
            "history_size": len(self._history),
        }

    # ─── Очистка ───
    def clear(self) -> None:
        """Сбросить подписки + историю (для тестов)."""
        self._subscribers.clear()
        self._history.clear()
        self._stats = {"published": 0, "delivered": 0, "dropped": 0}


# Глобальный singleton
_bus: AgentCANBus | None = None


def get_bus() -> AgentCANBus:
    """Получить глобальную шину (lazy singleton)."""
    global _bus
    if _bus is None:
        _bus = AgentCANBus()
    return _bus


def reset_bus() -> None:
    """Сбросить singleton (для тестов)."""
    global _bus
    _bus = None


__all__ = [
    "AgentCANBus", "Message", "get_bus", "reset_bus",
    "HISTORY_SIZE", "_matches",
]
