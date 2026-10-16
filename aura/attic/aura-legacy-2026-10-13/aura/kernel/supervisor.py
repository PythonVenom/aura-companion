"""Supervisor — следит, перезапускает, отключает.
'Let it crash' — Erlang/OTP philosophy.
"""
import asyncio
import logging
from collections.abc import Callable

log = logging.getLogger("aura.supervisor")

MAX_RESTARTS = 3


class Supervisor:
    def __init__(self, bus, registry):
        self.bus = bus
        self.registry = registry
        self._tasks: dict[str, asyncio.Task] = {}

    def spawn(self, name: str, coro_factory: Callable):
        async def _watch():
            while True:
                organ = self.registry.get(name)
                if organ is None or organ.restarts >= MAX_RESTARTS:
                    log.error("organ %s disabled (restarts=%s)",
                              name, organ.restarts if organ else "?")
                    self.registry.unregister(name)
                    return
                try:
                    log.info("starting organ: %s", name)
                    await coro_factory()
                except asyncio.CancelledError:
                    log.info("organ %s cancelled", name)
                    return
                except Exception as e:
                    organ.restarts += 1
                    organ.status = "crashed"
                    log.exception("organ %s crashed (%s/%s): %s",
                                  name, organ.restarts, MAX_RESTARTS, e)
                    await self.bus.publish("organ.crashed",
                                           {"name": name, "error": str(e)})
                    await asyncio.sleep(1.0)

        self.registry.register(name)
        task = asyncio.create_task(_watch(), name=f"supervisor:{name}")
        self._tasks[name] = task
        return task

    async def shutdown(self):
        for _name, task in self._tasks.items():
            task.cancel()
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
