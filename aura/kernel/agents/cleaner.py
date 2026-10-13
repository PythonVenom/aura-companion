"""Cleaner Agent — авто-сортировка + чистка мусора."""
import logging
import os
from pathlib import Path

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log

log = logging.getLogger("aura.agents.cleaner")


class CleanerAgent:
    name = "cleaner"
    version = "0.1.0"

    def __init__(self, dry_run: bool = True):
        self.ctx = None
        self._running = False
        self.dry_run = dry_run

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        ctx.bus.subscribe("cleaner.scan", self._on_scan)
        ctx.bus.subscribe("cleaner.aura", self._on_aura_clean)
        log.info("cleaner started (dry_run=%s)", self.dry_run)
        event_log.append("agent.started",
                         {"name": self.name, "dry_run": self.dry_run},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _on_scan(self, event) -> None:
        d = Path.home() / "Загрузки"
        if not d.exists():
            d = Path.home() / "Downloads"
        if not d.exists():
            text = "Папка загрузок не найдена."
        else:
            files = [f for f in d.iterdir() if f.is_file()]
            text = f"В загрузках {len(files)} файлов. Dry-run: {self.dry_run}"
        event_log.append("cleaner.scan", {"text": text}, src=self.name)
        if self.ctx:
            await self.ctx.bus.publish("speaker.say", {"text": text})

    async def _on_aura_clean(self, event) -> None:
        import glob
        removed = 0
        for pattern in ("/tmp/aura_speech_*.wav",):
            for f in glob.glob(pattern):
                if not self.dry_run:
                    try:
                        os.unlink(f)
                        removed += 1
                    except OSError:
                        pass
                else:
                    removed += 1
        text = f"Cleaner: {removed} временных файлов Aura."
        event_log.append("cleaner.aura", {"removed": removed}, src=self.name)
        if self.ctx:
            await self.ctx.bus.publish("speaker.say", {"text": text})

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "dry_run": self.dry_run}

    async def stop(self) -> None:
        self._running = False
        if self.ctx:
            for t in ("cleaner.scan", "cleaner.aura"):
                for h in list(self.ctx.bus._subs.get(t, [])):
                    self.ctx.bus.unsubscribe(t, h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
