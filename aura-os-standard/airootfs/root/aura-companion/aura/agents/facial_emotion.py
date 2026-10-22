"""AgentFacialEmotion — распознавание эмоций по лицу.

Наука: EmoNet (Kosti 2019), FER2013, MediaPipe Face Mesh.
Назначение: батя молчит, но лицо болит → AURA звонит врачу.
"""
from __future__ import annotations

from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentFacialEmotion(BaseAgent):
    name = "facial_emotion"
    MODULE_ALWAYS = True
    FRAME_PATH = Path.home() / ".cache" / "aura" / "camera_frame.jpg"

    # Упрощённая карта (без ML-модели, только Face Mesh landmarks)
    PAIN_KEYWORDS = ("боль", "болит", "плохо")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(k in t for k in (
            "какое у меня лицо", "моя эмоция", "что на моём лице",
            "проверь моё лицо", "я выгляжу",
        ))

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        ok, result = self._analyze()
        if ok:
            return AgentResponse.ok(text=result, agent_name=self.name)
        return AgentResponse.ok(text=f"❌ {result}", agent_name=self.name)

    def _analyze(self) -> tuple[bool, str]:
        try:
            import cv2
            import mediapipe as mp
        except ImportError as e:
            return False, f"зависимости: {e}"
        if not self.FRAME_PATH.exists():
            return False, "нет кадра (сначала: «сделай фото»)"
        try:
            img = cv2.imread(str(self.FRAME_PATH))
            if img is None:
                return False, "кадр не читается"
            # mediapipe 1.1.x: solutions может быть недоступен
            try:
                mp_face = mp.solutions.face_mesh
                with mp_face.FaceMesh(static_image_mode=True) as mesh:
                    res = mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                if not res.multi_face_landmarks:
                    return False, "лицо не найдено"
                n_faces = len(res.multi_face_landmarks)
                return True, f"👁️ Лиц найдено: {n_faces}. (ML-эмоции — задел)"
            except AttributeError:
                # Fallback: каскад Хаара (OpenCV)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                cascade = cv2.CascadeClassifier(
                    str(getattr(getattr(cv2, "data", None), "haarcascades", "")) + "haarcascade_frontalface_default.xml"
                )
                faces = cascade.detectMultiScale(gray, 1.3, 5)
                if len(faces) == 0:
                    return False, "лицо не найдено (Haar)"
                return True, f"👁️ Лиц найдено: {len(faces)} (Haar). ML — задел."
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"


__all__ = ["AgentFacialEmotion"]
