"""#134 + #145 AgentVisualAnalysis — «что на экране?» + LLM-описание.

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

        # #145: LLM-описание (если brain доступен)
        description = self._describe_with_llm(ocr_text)

        if description:
            return f"👁️ {description}"

        # Fallback: OCR preview
        preview = ocr_text[:500].strip()
        lines = len(ocr_text.splitlines())
        return f"👁️ Экран ({lines} строк):\n\n{preview}"

    def _describe_with_llm(self, ocr_text: str) -> str:
        """#145: краткое описание экрана через brain.

        Fallback: пустая строка если LLM недоступен.
        """
        if not ocr_text.strip():
            return ""
        try:
            from aura.agents.brain import AgentBrain
            brain = AgentBrain()
            prompt = (
                "Кратко опиши что на экране пользователя (1-2 предложения). "
                "Только суть, без воды.\n\n"
                f"Текст с экрана:\n{ocr_text[:1500]}"
            )
            description = brain.ask(prompt)
            if description and not description.startswith("❌"):
                return description.strip()
        except Exception:
            pass
        return ""


__all__ = ["AgentVisualAnalysis"]
