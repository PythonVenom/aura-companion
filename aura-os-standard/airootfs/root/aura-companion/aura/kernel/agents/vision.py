"""Vision Agent v2.0 — камера через asyncio.run_in_executor.
Без daemon-thread → нет C++ abort при shutdown.
Наука: Edge AI, Motion Detection (OpenCV).
"""
import asyncio
import contextlib
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log

log = logging.getLogger("aura.agents.vision")

CAMERA = os.environ.get("AURA_CAMERA", "/dev/video0")
MOTION_THRESHOLD = 5000
FRAME_INTERVAL = 0.5


class VisionAgent:
    name = "vision"
    version = "2.0.0"

    def __init__(self, camera: str = CAMERA):
        self.ctx: AgentContext | None = None
        self._running = False
        self._camera = camera
        self._task: asyncio.Task | None = None
        self._cap = None
        self._last_motion_ts = 0.0
        self._mute_until = 0.0
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="vision")

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True

        if not os.path.exists(self._camera):
            log.warning("vision: камера %s не найдена", self._camera)
            event_log.append("vision.unavailable",
                             {"camera": self._camera}, src=self.name)
            return

        ctx.bus.subscribe("voice.wake", self._on_voice_wake)
        self._task = asyncio.create_task(self._capture_loop())
        log.info("vision started (%s)", self._camera)
        event_log.append("agent.started",
                         {"name": self.name, "v": self.version,
                          "camera": self._camera},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    def _read_frame(self, cap):
        """Sync-функция: читает кадр в executor."""
        return cap.read()

    async def _capture_loop(self):
        try:
            import cv2
        except ImportError:
            log.warning("vision: cv2 не установлен")
            return

        loop = asyncio.get_running_loop()
        self._cap = cv2.VideoCapture(self._camera)
        if not self._cap.isOpened():
            log.warning("vision: не удалось открыть %s", self._camera)
            return

        # AURA_VISION_BUFFER_V1: минимальный буфер → меньше лага
        with contextlib.suppress(Exception):
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        prev_frame = None
        try:
            while self._running:
                ret, frame = await loop.run_in_executor(
                    self._executor, self._read_frame, self._cap)
                if not ret:
                    await asyncio.sleep(FRAME_INTERVAL)
                    continue

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)

                if prev_frame is not None:
                    delta = cv2.absdiff(prev_frame, gray)
                    thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
                    changed = cv2.countNonZero(thresh)
                    now = time.monotonic()
                    if changed > MOTION_THRESHOLD and (now - self._last_motion_ts) > 5.0:
                        self._last_motion_ts = now
                        log.info("vision: motion detected (changed=%d)", changed)
                        await self._publish_motion(changed)

                prev_frame = gray
                await asyncio.sleep(FRAME_INTERVAL)
        except asyncio.CancelledError:
            log.info("vision: cancelled")
            raise
        except Exception as e:
            log.exception("vision loop error: %s", e)
        finally:
            # AURA_VISION_CLEANUP_V1: освобождаем камеру в том же потоке
            if self._cap is not None:
                with contextlib.suppress(Exception):
                    await loop.run_in_executor(
                        self._executor, self._cap.release)
                self._cap = None
            log.info("vision capture loop stopped")

    async def _on_voice_wake(self, event) -> None:
        """AURA_VISION_MUTE_DIALOG_V1: молчим 15 сек пока батя говорит с Aura."""
        import time as _t
        self._mute_until = _t.monotonic() + 15.0
        log.debug("vision: muted 15s (voice dialog)")

    async def _publish_motion(self, changed: int):
        if not self.ctx:
            return
        # AURA_VISION_MUTE_DIALOG_V1: не мешаем диалогу
        import time as _t
        if _t.monotonic() < self._mute_until:
            return
        event_log.append("vision.motion",
                         {"changed": changed, "camera": self._camera},
                         src=self.name)
        await self.ctx.bus.publish("vision.motion",
                                   {"changed": changed,
                                    "camera": self._camera})

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "version": self.version,
                "camera": self._camera}

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(TimeoutError, asyncio.CancelledError):
                await asyncio.wait_for(self._task, timeout=3.0)
        self._executor.shutdown(wait=False)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
