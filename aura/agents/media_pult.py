"""
Агент медиа-пульта (AgentMediaPult).

YouTube (firefox --new-window) + управление через playerctl.
stop / play для текущего медиа-плеера.

Мигрирован из agents/media_pult.py (монолит, мёртвый по ADR-004).
Изменения:
- Контракт BaseAgent: can_handle / handle
- Guard can_handle в начале handle
- Логика play_youtube / stop_media / continue_media НЕ менялась

Портирован как заготовка (Фаза 6). НЕ подключён к bootstrap.
См. ADR-004.

СВЯЗЬ: дубль media_search (play/stop). Но media_pult умеет playerctl
напрямую (VLC/mpv/браузер) — media_search ходит через файлы.
Решить при подключении.
"""

from __future__ import annotations

import subprocess

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentMediaPult(BaseAgent):
    """YouTube + playerctl-управление."""

    name = "media_pult"

    YOUTUBE_URL = "https://www.youtube.com/watch?v="

    KEYWORDS = (
        "включи ютуб",
        "включи youtube",
        "стоп медиа",
        "останови медиа",
        "продолжи медиа",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(agent_name=self.name)

        cmd = request.text.lower()

        if "включи ютуб" in cmd or "включи youtube" in cmd:
            video_id = self._extract_video_id(cmd)
            return AgentResponse.ok(
                text=self.play_youtube(video_id),
                agent_name=self.name,
            )

        if "стоп медиа" in cmd or "останови медиа" in cmd:
            return AgentResponse.ok(text=self.stop_media(), agent_name=self.name)

        if "продолжи медиа" in cmd:
            return AgentResponse.ok(
                text=self.continue_media(), agent_name=self.name,
            )

        return AgentResponse.not_handled(agent_name=self.name)

    def play_youtube(self, video_id: str) -> str:
        try:
            subprocess.Popen(
                ["firefox", "--new-window", self.YOUTUBE_URL + video_id],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return "🎬 YouTube включён (в фоне)"
        except Exception:
            return "🎬 Не удалось включить YouTube"

    def stop_media(self) -> str:
        try:
            subprocess.run(
                ["playerctl", "stop"], capture_output=True, timeout=3,
            )
            return "⏹️ Все источники звука остановлены."
        except Exception:
            return "⏹️ Не удалось остановить медиа."

    def continue_media(self) -> str:
        try:
            subprocess.run(
                ["playerctl", "play"], capture_output=True, timeout=3,
            )
            return "▶️ Медиа продолжено."
        except Exception:
            return "▶️ Не удалось продолжить медиа."

    def _extract_video_id(self, cmd: str) -> str:
        for word in ("включи ютуб", "включи youtube"):
            if word in cmd:
                rest = cmd.replace(word, "").strip()
                if rest:
                    return rest.split()[0]
        return "dQw4w9WgXcQ"


__all__ = ["AgentMediaPult"]
