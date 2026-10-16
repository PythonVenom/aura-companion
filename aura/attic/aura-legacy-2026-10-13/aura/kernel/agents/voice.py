"""Voice Agent — микрофон → STT → voice.heard.
Обёртка над AgentListener (T-one sherpa-onnx).
Наука: Voice Loop (Pieraccini 2012), Adapter Pattern.
"""
import asyncio
import logging
import threading
import time

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log

log = logging.getLogger("aura.agents.voice")


class VoiceAgent:
    name = "voice"
    version = "1.1.0"

    # Wake words (нижний регистр, подстрока)
    WAKE_WORDS = ("аура", "ура,", " аура", "ауру", "ауры")
    # Активное окно после wake — сколько секунд слушаем команду
    ACTIVE_WINDOW_SEC = 10.0

    def __init__(self, listen_timeout: float = 6.0):
        self.ctx: AgentContext | None = None
        self._running = False
        self._listener = None
        self._thread = None
        self._loop = None
        self._listen_timeout = listen_timeout
        self._active_until: float = 0.0
        self._speaker_active = False

    def _has_wake(self, text: str) -> bool:
        t = text.lower()
        return any(w in t for w in self.WAKE_WORDS)

    def _in_active_window(self) -> bool:
        import time as _t
        return _t.monotonic() < self._active_until

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        self._loop = asyncio.get_running_loop()

        from aura.agents.listener import AgentListener
        self._listener = AgentListener()
        # AURA_LISTENER_ACTIVATE_V1: без activate() listen() возвращает None
        if hasattr(self._listener, "activate"):
            self._listener.activate()
            log.info("voice: listener activated")

        if not self._listener.ready:
            log.warning("voice: T-one не готов — voice выключен")
            event_log.append("voice.unavailable",
                             {"reason": "t-one not ready"}, src=self.name)
            return

        # AURA_ECHO_PAUSE_V1: пауза микрофона, пока Aura говорит
        ctx.bus.subscribe("speaker.started", self._on_speaker_start)
        ctx.bus.subscribe("speaker.spoken", self._on_speaker_done)

        # AURA_VOICE_RESET_PAUSE_V1: сбрасываем _paused при старте
        if self._listener and hasattr(self._listener, "resume"):
            self._listener.resume()
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        log.info("voice started (timeout=%.1fs, paused=%s)",
                 self._listen_timeout,
                 getattr(self._listener, "_paused", "?"))
        event_log.append("agent.started",
                         {"name": self.name, "v": self.version,
                          "listener_ready": self._listener.ready,
                          "timeout": self._listen_timeout},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _on_speaker_start(self, event) -> None:
        """Aura начала говорить — пауза микрофона."""
        self._speaker_active = True
        if self._listener and hasattr(self._listener, "pause"):
            self._listener.pause()
        log.info("voice: paused (speaker active)")

    async def _on_speaker_done(self, event) -> None:
        """Aura закончила — снимаем паузу через 0.5 сек."""
        import asyncio as _a
        await _a.sleep(2.5)  # AURA_ECHO_TAIL_V2  # AURA_ECHO_TAIL_V1: elder-care медленная речь
        self._speaker_active = False
        if self._listener and hasattr(self._listener, "resume"):
            self._listener.resume()
        log.info("voice: resumed")

    def _listen_loop(self):
        """Цикл: listen() → текст → шина → повтор.
        AURA_VOICE_ROBUST_V1: force-resume если paused > 15s.
        """
        log.info("voice listen loop started")
        import time as _t
        paused_since = None
        while self._running:
            # AURA_VOICE_FORCE_RESUME_V1: если listener застрял в pause — снимаем
            if self._listener and getattr(self._listener, "_paused", False):
                if paused_since is None:
                    paused_since = _t.monotonic()
                elif _t.monotonic() - paused_since > 15.0:
                    log.warning("voice: force-resume (paused >15s)")
                    if hasattr(self._listener, "resume"):
                        self._listener.resume()
                    paused_since = None
                _t.sleep(0.3)
                continue
            else:
                paused_since = None

            try:
                text = self._listener.listen(timeout=self._listen_timeout)
                if not text:
                    continue
                text = text.strip()
                if not text:
                    continue
                log.info("voice heard: %s", text[:100])
                asyncio.run_coroutine_threadsafe(
                    self._publish_heard(text),
                    self._loop,
                )
            except Exception as e:
                log.exception("voice listen error: %s", e)
                time.sleep(0.5)
        log.info("voice listen loop stopped")

    async def _publish_heard(self, text: str):
        if not self.ctx:
            return
        import time as _t

        # AURA_VOICE_NO_SELF_V1: не слушаем себя
        if self._speaker_active:
            event_log.append("voice.ignored",
                             {"text": text[:120], "reason": "speaker active"},
                             src=self.name)
            return

        has_wake = self._has_wake(text)
        in_window = self._in_active_window()

        # WANDER_VOICE_GATE_V1: реагируем только если есть wake ИЛИ активное окно
        if not (has_wake or in_window):
            event_log.append("voice.ignored",
                             {"text": text[:120], "reason": "no wake, no window"},
                             src=self.name)
            return

        # Если был wake — открываем/продлеваем окно
        if has_wake:
            self._active_until = _t.monotonic() + self.ACTIVE_WINDOW_SEC
            event_log.append("voice.wake",
                             {"text": text[:120],
                              "window_sec": self.ACTIVE_WINDOW_SEC},
                             src=self.name)
            # AURA_VOICE_WAKE_BUS_V1: публикуем в шину для vision.mute
            await self.ctx.bus.publish("voice.wake",
                                       {"text": text[:120],
                                        "window_sec": self.ACTIVE_WINDOW_SEC})

        event_log.append("voice.heard", {"text": text[:120]}, src=self.name)
        await self.ctx.bus.publish("voice.heard", {"text": text})
        # Батя говорил → не тишина
        await self.ctx.bus.publish("proactive.touch", {})

    async def health(self) -> dict:
        return {
            "status": "ok" if self._running else "stopped",
            "version": self.version,
            "listener_ready": self._listener.ready if self._listener else False,
        }

    async def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
