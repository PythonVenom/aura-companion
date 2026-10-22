"""AgentVideoAnalyzer — анализ видео (падения, движение).

Наука: SlowFast (Feichtenhofer 2019), YOLOv8.
Fallback без ML: сравнение кадров (OpenCV absdiff).
"""
from __future__ import annotations

from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentVideoAnalyzer(BaseAgent):
    name = "video_analyzer"
    MODULE_ALWAYS = True
    FRAME_PATH = Path.home() / ".cache" / "aura" / "camera_frame.jpg"
    PREV_PATH = Path.home() / ".cache" / "aura" / "camera_prev.jpg"

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(k in t for k in (
            "что в кадре", "анализ кадра", "есть движение",
            "детектор падения", "проверь движение",
        ))

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        ok, msg = self._analyze()
        if ok:
            return AgentResponse.ok(text=msg, agent_name=self.name)
        return AgentResponse.ok(text=f"❌ {msg}", agent_name=self.name)

    def _analyze(self) -> tuple[bool, str]:
        try:
            import cv2
        except ImportError:
            return False, "OpenCV не установлен"
        if not self.FRAME_PATH.exists():
            return False, "нет кадра (сначала «сделай фото»)"
        try:
            cur = cv2.imread(str(self.FRAME_PATH))
            if cur is None:
                return False, "кадр не читается"
            if self.PREV_PATH.exists():
                prev = cv2.imread(str(self.PREV_PATH))
                if prev is not None:
                    diff = cv2.absdiff(cur, prev)
                    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
                    motion = int((gray > 25).sum())
                    # Сохраняем текущий как prev
                    cv2.imwrite(str(self.PREV_PATH), cur)
                    return True, f"📹 Движение: {motion} пикс. ({'есть' if motion > 5000 else 'слабое'})"
            # Первый кадр — сохраняем как prev
            cv2.imwrite(str(self.PREV_PATH), cur)
            return True, "📹 Первый кадр сохранён (базлайн)"
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"


__all__ = ["AgentVideoAnalyzer"]
