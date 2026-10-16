"""KernelThread — async loop в отдельном потоке.

Наука: Concurrent Streams (XP), Thread + asyncio.
Main thread (sync, Orchestrator) <-> Kernel thread (async, event-driven).

Использование:
    kt = KernelThread()
    kt.start()
    kt.publish_sync("voice.heard", {"text": "привет"})
    kt.stop()
"""
from __future__ import annotations

import asyncio
import logging
import threading
from typing import Any

log = logging.getLogger("aura.kernel.thread")


class KernelThread:
    """Запускает AuraKernel в daemon-потоке с постоянным event loop."""

    def __init__(self) -> None:
        self.kernel: Any = None
        self.loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._stopped = False

    def start(self, timeout: float = 10.0) -> bool:
        """Запустить kernel. True = поднялся за timeout."""
        if self._thread is not None:
            return False
        from aura.kernel.bootstrap import AuraKernel
        self.kernel = AuraKernel()
        self._thread = threading.Thread(
            target=self._run, name="aura-kernel", daemon=True,
        )
        self._thread.start()
        ok = self._ready.wait(timeout=timeout)
        if ok:
            log.info("kernel thread ready")
        else:
            log.error("kernel thread start timeout (%.1fs)", timeout)
        return ok

    def _run(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.kernel.start())
            self._ready.set()
            self.loop.run_forever()
        except Exception as e:
            log.exception("kernel thread crashed: %s", e)
            self._ready.set()
        finally:
            try:
                self.loop.run_until_complete(self.kernel.stop())
            except Exception:
                pass
            self.loop.close()
            log.info("kernel thread stopped")

    def stop(self, timeout: float = 5.0) -> None:
        """Остановить kernel + loop."""
        if self._stopped:
            return
        self._stopped = True
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def publish_sync(self, topic: str, payload: dict) -> None:
        """Sync-вызов из main thread — публикует в kernel bus."""
        if not self.loop or not self.kernel:
            log.warning("publish_sync: kernel not ready")
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self.kernel.bus.publish(topic, payload), self.loop,
            )
        except Exception as e:
            log.warning("publish_sync failed: %s", e)

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def status(self) -> dict:
        if not self.kernel:
            return {"running": False}
        return {
            "running": self.is_alive(),
            "agents": len(self.kernel.registry.all()),
            "rules": len(self.kernel.router._rules),
        }
