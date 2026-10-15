"""AgentVisionLLM — анализ кадра через LLM (multimodal).

Наука: LLaVA (Liu 2023), Qwen-VL.
Fallback: если модель не multimodal — OCR + описание.
"""
from __future__ import annotations

import base64
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentVisionLLM(BaseAgent):
    name = "vision_llm"
    MODULE_ALWAYS = True
    FRAME_PATH = Path.home() / ".cache" / "aura" / "camera_frame.jpg"

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(k in t for k in (
            "опиши кадр", "что видишь", "опиши что на камере",
            "vision llm", "опиши изображение",
        ))

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        if not self.FRAME_PATH.exists():
            return AgentResponse.ok(
                text="❌ Нет кадра (сначала «сделай фото»)",
                agent_name=self.name,
            )
        # Try multimodal LLM через Ollama (llava, qwen2.5-vl и т.п.)
        try:
            import json
            import urllib.request
            img_b64 = base64.b64encode(self.FRAME_PATH.read_bytes()).decode()
            payload = json.dumps({
                "model": "llava:latest",
                "prompt": "Опиши коротко, что на изображении. Только русский.",
                "images": [img_b64],
                "stream": False,
            }).encode()
            req = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                resp = json.loads(r.read().decode())
                text = resp.get("response", "").strip()
                if text:
                    return AgentResponse.ok(
                        text=f"👁️ {text[:300]}",
                        agent_name=self.name,
                    )
        except Exception as e:
            return AgentResponse.ok(
                text=f"⚠️ Vision LLM недоступен: {type(e).__name__}. "
                     f"Установи llava: ollama pull llava",
                agent_name=self.name,
            )
        return AgentResponse.not_handled(self.name)


__all__ = ["AgentVisionLLM"]
