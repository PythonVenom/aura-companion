"""Aura Message Bus — нервная система.
Публикуй/подписывайся. Никаких прямых импортов между агентами.
Наука: Actor Model (Hewitt 1973), Erlang/OTP.
"""
import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

log = logging.getLogger("aura.bus")


class Bus:
    def __init__(self):
        self._subs: dict[str, list[Callable]] = defaultdict(list)
        self._queue: asyncio.Queue = asyncio.Queue()

    def subscribe(self, topic: str, handler: Callable):
        self._subs[topic].append(handler)
        log.info("subscribe: %s -> %s", topic, handler.__name__)

    def unsubscribe(self, topic: str, handler: Callable):
        if handler in self._subs[topic]:
            self._subs[topic].remove(handler)

    async def publish(self, topic: str, event: Any):
        await self._queue.put((topic, event))

    async def run(self):
        while True:
            topic, event = await self._queue.get()
            for handler in self._subs.get(topic, []):
                try:
                    result = handler(event)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    log.exception("handler %s failed on %s: %s",
                                  handler.__name__, topic, e)


bus = Bus()
