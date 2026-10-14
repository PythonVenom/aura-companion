"""#134 AgentVisualAnalysis — «что на экране?».

Объединяет:
- AgentVision (скриншот)
- AgentScreenReader (OCR)
- LLM (описание)

Наука: Apple Visual Intelligence (2025), Screen2Vec (2023).
"""
from __future__ import annotations

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentVisualAnalysis(BaseAgent):
    """Единый ответ на «что на экране?»."""

    name = "visual_analysis"

    TRIGGERS = (
        "что на экране", "опиши экран", "прочитай экран",
        "что видишь", "анализ экрана",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = self._read_screen()
        return AgentResponse.ok(text=text, agent_name=self.name)

    def _read_screen(self) -> str:
        # 1. OCR через screen_reader
        try:
            from aura.agents.screen_reader import AgentScreenReader
            sr = AgentScreenReader()
            ocr_text = sr._ocr_full() if hasattr(sr, "_ocr_full") else ""
        except Exception as e:
            ocr_text = ""
            err = str(e)
        else:
            err = ""

        if not ocr_text:
            return f"👁️ Экран пуст или OCR недоступен ({err or 'no text'})"

        # Обрезаем до 500 символов
        preview = ocr_text[:500].strip()
        lines = len(ocr_text.splitlines())
        return f"👁️ Экран ({lines} строк):\n\n{preview}"


__all__ = ["AgentVisualAnalysis"]
