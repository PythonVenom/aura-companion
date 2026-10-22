"""Audio Ducker — приглушает чужие аудиопотоки (VLC, Firefox), не Aura.
Наука: Audio Ducking, per-app volume (PipeWire/pactl).
"""
import asyncio
import contextlib
import logging
import subprocess

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log

log = logging.getLogger("aura.agents.audio_ducker")

DEFAULT_DUCK_VOLUME = 20


class AudioDuckerAgent:
    name = "audio_ducker"
    version = "1.1.0"

    def __init__(self, duck_volume: int = DEFAULT_DUCK_VOLUME):
        self.ctx: AgentContext | None = None
        self._running = False
        self._duck_volume = duck_volume
        self._saved_inputs: dict[int, int] = {}
        self._duck_until = 0.0
        self._watchdog_task = None

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        ctx.bus.subscribe("voice.wake", self._on_wake)
        ctx.bus.subscribe("speaker.started", self._on_speaker_start)
        ctx.bus.subscribe("speaker.spoken", self._on_speaker_done)
        ctx.bus.subscribe("ducker.resume", self._on_speaker_done)
        self._watchdog_task = asyncio.create_task(self._watchdog_loop())  # type: ignore[assignment]
        log.info("audio_ducker started (duck=%d%%)", self._duck_volume)
        event_log.append("agent.started",
                         {"name": self.name, "v": self.version,
                          "duck_volume": self._duck_volume},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    # ── PipeWire / pactl ────────────────────────────

    # AURA_DUCKER_SKIP_AEC_V1: не трогаем служебные потоки Aura/PipeWire
    SKIP_NAMES = ("echo-cancel", "Echo-Cancel", "aura-", "paplay")

    def _list_sink_inputs(self) -> list[tuple[int, int]]:
        """AURA_DUCKER_TAG_V2: skip по application.name=Aura (тег).
        Только чужие потоки — Firefox, VLC, итд.
        """
        result = []
        try:
            r = subprocess.run(
                ["pactl", "list", "sink-inputs"],
                capture_output=True, text=True, timeout=2,
            )
            streams: dict[int, dict] = {}
            current_id: int | None = None
            for line in r.stdout.splitlines():
                stripped = line.strip()
                if stripped.startswith("Sink Input #"):
                    try:
                        current_id = int(stripped.split("#")[1])
                        streams[current_id] = {"vol": None, "is_service": False}
                    except (ValueError, IndexError):
                        current_id = None
                    continue
                if current_id is None:
                    continue
                # AURA_TAG_V1: skip если application.name содержит Aura
                if "application.name" in stripped:
                    if "Aura" in stripped or any(s in stripped for s in self.SKIP_NAMES):
                        streams[current_id]["is_service"] = True
                elif stripped.startswith("node.name"):
                    if any(s in stripped for s in self.SKIP_NAMES):
                        streams[current_id]["is_service"] = True
                # Volume
                elif stripped.startswith("Volume:") and "front-left:" in stripped:
                    parts = stripped.split("/")
                    if len(parts) >= 2:
                        with contextlib.suppress(ValueError):
                            streams[current_id]["vol"] = int(
                                parts[1].strip().replace("%", ""))

            for sid, info in streams.items():
                if info["is_service"]:
                    continue
                if info["vol"] is not None:
                    result.append((sid, info["vol"]))
        except Exception as e:
            log.debug("list sink-inputs failed: %s", e)
        return result

    def _set_sink_input_volume(self, input_id: int, percent: int) -> bool:
        try:
            subprocess.run(
                ["pactl", "set-sink-input-volume", str(input_id), f"{percent}%"],
                capture_output=True, timeout=2,
            )
            return True
        except Exception as e:
            log.debug("set-sink-input-volume failed: %s", e)
            return False

    # ── Handlers ────────────────────────────────────

    async def _on_wake(self, event) -> None:
        if self._saved_inputs:
            return
        inputs = self._list_sink_inputs()
        if not inputs:
            log.debug("duck: нечего приглушать")
            return
        for input_id, vol in inputs:
            self._saved_inputs[input_id] = vol
            self._set_sink_input_volume(input_id, self._duck_volume)
        import time as _t
        self._duck_until = _t.monotonic() + 3.0  # AURA_WATCHDOG_V2
        log.info("duck: %d streams → %d%%", len(self._saved_inputs), self._duck_volume)
        event_log.append("audio.ducked",
                         {"count": len(self._saved_inputs), "to": self._duck_volume},
                         src=self.name)

    async def _on_speaker_start(self, event) -> None:
        if self._saved_inputs:
            return
        import time as _t
        inputs = self._list_sink_inputs()
        for input_id, vol in inputs:
            self._saved_inputs[input_id] = vol
            self._set_sink_input_volume(input_id, self._duck_volume)
        if self._saved_inputs:
            self._duck_until = _t.monotonic() + 3.0
            print(f"[ducker] started duck: {len(self._saved_inputs)} streams")

    async def _on_speaker_done(self, event) -> None:
        print(f"[ducker] _on_speaker_done: saved={len(self._saved_inputs)}")
        if not self._saved_inputs:
            return
        for input_id, vol in self._saved_inputs.items():
            ok = self._set_sink_input_volume(input_id, vol)
            print(f"[ducker]   resume id={input_id} vol={vol}% ok={ok}")
        log.info("resume: %d streams", len(self._saved_inputs))
        event_log.append("audio.resumed",
                         {"count": len(self._saved_inputs)}, src=self.name)
        self._saved_inputs.clear()

    async def _watchdog_loop(self):
        """AURA_DUCKER_WATCHDOG_V1: если resume не пришёл за 30с — force."""
        import time as _t
        while self._running:
            await asyncio.sleep(5.0)
            if not self._saved_inputs:
                continue
            if _t.monotonic() > self._duck_until > 0:
                log.warning("ducker watchdog: force-resume (no speaker.spoken)")
                await self._on_speaker_done(None)

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "version": self.version,
                "duck_volume": self._duck_volume}

    async def stop(self) -> None:
        self._running = False
        if self._watchdog_task:
            self._watchdog_task.cancel()
        for input_id, vol in self._saved_inputs.items():
            self._set_sink_input_volume(input_id, vol)
        self._saved_inputs.clear()
        if self.ctx:
            for t in ("voice.wake", "speaker.started", "speaker.spoken"):
                for h in list(self.ctx.bus._subs.get(t, [])):
                    self.ctx.bus.unsubscribe(t, h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
