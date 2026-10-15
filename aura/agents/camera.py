"""AgentCamera — видеопоток с камеры (/dev/video0).

Наука: Video4Linux2, OpenCV, GStreamer.
Назначение: захват кадров для elder-care (падения, жесты, эмоции).
"""
from __future__ import annotations

import time
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentCamera(BaseAgent):
    name = "camera"
    MODULE_ALWAYS = True
    FRAME_PATH = Path.home() / ".cache" / "aura" / "camera_frame.jpg"

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(k in t for k in (
            "сделай фото", "снимок с камеры", "фото с камеры",
            "посмотри в камеру", "что видно в камере",
        ))

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        ok, path_or_err = self._grab_frame()
        if ok:
            try:
                from aura.core import blackboard as bb
                bb.post_task("camera", "captured", f"frame: {path_or_err}")
            except Exception:
                pass
            return AgentResponse.ok(
                text=f"📸 Кадр сохранён: {path_or_err}",
                agent_name=self.name,
            )
        return AgentResponse.ok(
            text=f"❌ Камера: {path_or_err}",
            agent_name=self.name,
        )

    def _grab_frame(self) -> tuple[bool, str]:
        try:
            import cv2
        except ImportError:
            return False, "OpenCV не установлен"
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return False, "/dev/video0 недоступен"
            # Прогрев (первый кадр часто чёрный)
            for _ in range(3):
                cap.read()
                time.sleep(0.05)
            ok, frame = cap.read()
            cap.release()
            if not ok or frame is None:
                return False, "не удалось захватить кадр"
            self.FRAME_PATH.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(self.FRAME_PATH), frame)
            return True, str(self.FRAME_PATH)
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"


__all__ = ["AgentCamera"]
