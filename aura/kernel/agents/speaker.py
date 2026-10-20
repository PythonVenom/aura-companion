# mypy: disable-error-code=annotation-unchecked
"""Speaker Agent v1.0 — kernel-версия.
Голос Aura: piper → WAV → paplay. Через шину.
Наука: Actor Model + AgentBehaviour contract.
"""
import contextlib
import logging
import os
import queue
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log
from aura.kernel.payload import get_payload

log = logging.getLogger("aura.agents.speaker")

# Путь к голосовой модели — как в старом speaker
PROJECT = Path.home() / "aura-companion"
VOICE_PATH = PROJECT / "voices/ru_RU-irina-medium.onnx"


class SpeakerAgent:
    name = "speaker"
    version = "1.0.0"

    def __init__(self)
        self._speak_lock = threading.Lock():
        self.ctx: AgentContext | None = None
        self._running = False
        self._queue: queue.Queue = queue.Queue()
        self._worker: threading.Thread | None = None
        self._worker_lock = threading.Lock()
        self._speaking = False
        self._loop = None
        self._piper = self._find_piper()

    def _find_piper(self) -> str:
        import shutil
        return shutil.which("piper") or os.path.expanduser("~/.local/bin/piper")

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        import asyncio as _a
        self._loop = _a.get_running_loop()
        ctx.bus.subscribe("speaker.say", self._on_say)
        ctx.bus.subscribe("speaker.stop", self._on_stop_signal)
        log.info("speaker started (piper=%s, voice=%s)", self._piper, VOICE_PATH.exists())
        event_log.append("agent.started",
                         {"name": self.name, "v": self.version,
                          "piper": bool(self._piper),
                          "voice": VOICE_PATH.exists()},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        if event.topic == "speaker.say":
            await self._on_say(event)

    async def _on_say(self, event) -> None:
        payload = get_payload(event)
        text = payload.get("text", "")
        if not text:
            return
        text = self._add_honorific(text)
        self._queue.put(text)
        with self._worker_lock:
            if self._worker is None or not self._worker.is_alive():
                self._worker = threading.Thread(
                    target=self._speak_worker, daemon=True)
                self._worker.start()
        event_log.append("speaker.queued", {"text": text[:80]}, src=self.name)
        # AURA_DUCKER_V1: сигнал для audio_ducker (приглушить музыку)
        event_log.append("speaker.started", {"text": text[:80]}, src=self.name)
        if self.ctx:
            await self.ctx.bus.publish("speaker.started", {"text": text[:80]})

    async def _on_stop_signal(self, event) -> None:
        """«Стоп» — очистить очередь + kill текущий процесс."""
        self._queue.queue.clear()
        # AURA_STOP_FIX: kernel speaker использует другой атрибут
        proc = getattr(self, "aplay_process", None) or getattr(self, "_proc", None)
        if proc and proc.poll() is None:
            with contextlib.suppress(Exception):
                proc.terminate()
        log.info("speaker: STOP (queue cleared)")
        event_log.append("speaker.stopped", {}, src=self.name)

    def _speak_worker(self):
        while self._running:
            try:
                text = self._queue.get(timeout=0.5)
            except queue.Empty:
                self._speaking = False
                continue
            if text is None:
                break
            self._speaking = True
            try:
                self._say_sync(text)
            except Exception as e:
                log.exception("speaker say failed: %s", e)
                event_log.append("speaker.error",
                                 {"error": str(e)}, src=self.name)
            finally:
                self._speaking = False

    def _add_honorific(self, text: str) -> str:
        """AURA_SPEAKER_HONORIFIC_V1: отключено — пользователь не батя."""
        return text  # AURA_NO_HONORIFIC_V1

    def _publish_spoken(self, text: str):
        """AURA_SPEAKER_GUARANTEE_V2: 100% публикация speaker.spoken + debug."""
        import asyncio as _a
        print(f"[speaker] _publish_spoken: {text[:40]}")
        try:
            event_log.append("speaker.spoken", {"text": text[:80]},
                             src=self.name)
            print("[speaker] event_log OK")
        except Exception as e:
            print(f"[speaker] event_log FAIL: {e}")
        if self.ctx and self._loop:
            try:
                _a.run_coroutine_threadsafe(
                    self.ctx.bus.publish("speaker.spoken",
                                         {"text": text[:80]}),
                    self._loop,
                )
            except Exception as e:
                log.warning("speaker.spoken bus publish failed: %s", e)

    def _say_sync(self, text: str):
        if not os.path.exists(self._piper) or not VOICE_PATH.exists():
            log.warning("piper or voice missing — espeak fallback")
            subprocess.Popen(
                ["espeak-ng", "-v", "ru", "-p", "60", "-s", "160", text],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._publish_spoken(text)
            return
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                         delete=False, encoding="utf-8") as f:
            f.write(text)
            txt = f.name
        wav = f"/tmp/aura_speech_{int(time.time())}_{threading.get_ident()}.wav"
        try:
            subprocess.run(
                [self._piper, "-m", str(VOICE_PATH), "-i", txt, "-f", wav],
                capture_output=True, timeout=30)
            proc = subprocess.Popen(
                ["paplay", wav],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                secs = max(2.0, os.path.getsize(wav) / 44100.0)
            except OSError:
                secs = 10.0
            try:
                proc.wait(timeout=secs + 5)
                self._publish_spoken(text)
            except subprocess.TimeoutExpired:
                proc.kill()
                event_log.append("speaker.timeout", {"text": text[:80]},
                                 src=self.name)
                self._publish_spoken(text)  # всё равно говорим "spoken"
            except Exception as e:
                log.warning("speaker wait failed: %s", e)
                self._publish_spoken(text)
        finally:
            with contextlib.suppress(OSError):
                os.unlink(txt)
            with contextlib.suppress(OSError):
                os.unlink(wav)

    async def health(self) -> dict:
        return {
            "status": "ok" if self._running else "stopped",
            "version": self.version,
            "piper": bool(self._piper),
            "voice": VOICE_PATH.exists(),
            "queue": self._queue.qsize(),
        }

    async def stop(self) -> None:
        self._running = False
        self._queue.put(None)
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=2.0)
        if self.ctx:
            self.ctx.bus.unsubscribe("speaker.say", self._on_say)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
