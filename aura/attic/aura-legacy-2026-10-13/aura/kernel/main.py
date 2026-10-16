"""Aura Kernel — точка входа для systemd.
Запускает ядро + органеллы. Graceful shutdown по SIGTERM.
Наука: Composition Root + Systemd supervision.
"""
import asyncio
import logging
import signal
import sys

from aura.kernel.bootstrap import AuraKernel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
log = logging.getLogger("aura.kernel.main")


async def _run():
    kernel = AuraKernel()
    await kernel.start()
    log.info("AURA KERNEL UP: %s", kernel.status()["organs"])

    stop = asyncio.Event()

    def _on_signal(sig):
        log.info("signal %s → graceful shutdown", sig)
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _on_signal, sig)

    await stop.wait()
    await kernel.stop()
    log.info("AURA KERNEL DOWN")


def main():
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        log.info("interrupted")
        sys.exit(0)


if __name__ == "__main__":
    main()
