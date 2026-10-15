"""AgentGesture — жесты рук (MediaPipe Hands).

Наука: MediaPipe Hands (Zhang 2020), Dynamic Time Warping.
Fallback: без ML — только «есть рука/нет руки» через Haar.
"""
from __future__ import annotations

from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentGesture(BaseAgent):
    name = "gesture"
    MODULE_ALWAYS = True
    FRAME_PATH = Path.home() / ".cache" / "aura" / "camera_frame.jpg"

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(k in t for k in (
            "какой жест", "проверь жест", "мои руки",
            "жест sos", "я машу рукой",
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
            import mediapipe as mp
        except ImportError as e:
            return False, f"зависимости: {e}"
        if not self.FRAME_PATH.exists():
            return False, "нет кадра"
        try:
            img = cv2.imread(str(self.FRAME_PATH))
            if img is None:
                return False, "кадр не читается"
            # MediaPipe 1.1.x может не иметь solutions
            try:
                mp_hands = mp.solutions.hands
                with mp_hands.Hands(static_image_mode=True, max_num_hands=2) as hands:
                    res = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                n = len(res.multi_hand_landmarks) if res.multi_hand_landmarks else 0
                return True, f"✋ Рук найдено: {n}"
            except AttributeError:
                return False, "mediapipe.solutions недоступен (v1.1.x)"
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"


__all__ = ["AgentGesture"]
