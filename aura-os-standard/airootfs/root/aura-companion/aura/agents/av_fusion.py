"""AgentAudioVisualFusion — синтез аудио + видео.

Наука: AV-HuBERT (Shi 2022), Multimodal Fusion (Baltrušaitis 2019).
Собирает сигналы других агентов (Camera, VideoAnalyzer, FacialEmotion,
Listener) и создаёт объединённое событие.
"""
from __future__ import annotations

from aura.core import blackboard as bb
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentAudioVisualFusion(BaseAgent):
    name = "av_fusion"
    MODULE_ALWAYS = True

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(k in t for k in (
            "общая картина", "что происходит вокруг",
            "синтез аудио видео", "все сигналы",
        ))

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        snap = bb.snapshot()
        alerts = bb.recent_alerts(window_sec=300)
        tasks = bb.active_tasks()
        lines = ["🎥 Аудио-визуальный синтез:"]
        lines.append(f"  Сектор: {snap.get('sector', 'unknown')}")
        lines.append(f"  Тревог: {len(alerts)}")
        lines.append(f"  Задач: {len(tasks)}")
        if alerts:
            for a in alerts[:3]:
                lines.append(f"    • {a['agent']}: {a['text'][:50]}")
        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)


__all__ = ["AgentAudioVisualFusion"]
