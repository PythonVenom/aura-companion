"""
Агент истории окон (AgentContextMemory).

Сканирует окна через wmctrl -l, сохраняет историю.
Ищет последний источник медиа (youtube/vlc/spotify).

Мигрирован из agents/context_memory.py (монолит, мёртвый по ADR-004).
Изменения:
- Контракт BaseAgent: can_handle / handle
- Автоопределение Wayland (_detect_wayland)
- Логика scan_windows / _detect_process / sort_by_time НЕ менялась

Портирован как заготовка (Фаза 6). НЕ подключён к bootstrap.
См. ADR-004.
"""

from __future__ import annotations

import os
import subprocess
import time

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


def _detect_wayland() -> bool:
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


class AgentContextMemory(BaseAgent):
    """История окон + последний источник медиа."""

    name = "context_memory"

    KEYWORDS = (
        "открытые окна",
        "история окон",
        "последний источник",
        "откуда музыка",
    )

    def __init__(self) -> None:
        self.is_wayland = _detect_wayland()
        self.ready = not self.is_wayland
        self.window_history: list[dict] = []
        self.last_played_source = None

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(agent_name=self.name)

        if self.is_wayland:
            return AgentResponse.ok(
                text="❌ История окон недоступна в Wayland",
                agent_name=self.name,
            )

        self.scan_windows()
        cmd = request.text.lower()

        if "источник" in cmd or "откуда" in cmd:
            source = self.get_last_media_source()
            if source:
                title = source.get("title", "")
                return AgentResponse.ok(
                    text=f"🎵 Последний источник: {title[:50]}",
                    agent_name=self.name,
                )
            return AgentResponse.ok(
                text="❌ Нет активного источника звука",
                agent_name=self.name,
            )

        windows = self.sort_by_time()
        if not windows:
            return AgentResponse.ok(
                text="🪟 Открытых окон нет",
                agent_name=self.name,
            )

        lines = ["🪟 Открытые окна:"]
        now = time.time()
        for w in windows:
            title = w.get("title", "")[:40]
            process = w.get("process", "")
            age = int(now - w.get("opened_at", now))
            lines.append(f"  • {title} ({age}с, {process})")
        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)

    def scan_windows(self) -> bool:
        if self.is_wayland:
            return False
        try:
            result = subprocess.run(
                ["wmctrl", "-l"], capture_output=True, text=True, timeout=3,
            )
            current_time = time.time()
            self.window_history = []
            for line in result.stdout.split("\n"):
                if not line.strip():
                    continue
                parts = line.split(None, 4)
                if len(parts) < 5:
                    continue
                window_id = parts[0]
                title = parts[4]
                self.window_history.append({
                    "id": window_id,
                    "title": title,
                    "opened_at": current_time,
                    "process": self._detect_process(title),
                })
            return True
        except Exception:
            return False

    def _detect_process(self, title: str) -> str:
        t = title.lower()
        if "youtube" in t or "ютуб" in t:
            return "youtube"
        if "vlc" in t or "media" in t:
            return "vlc"
        if "spotify" in t:
            return "spotify"
        if "firefox" in t or "браузер" in t:
            return "browser"
        if "code" in t or "код" in t:
            return "code"
        return "unknown"

    def get_last_media_source(self) -> dict | None:
        self.scan_windows()
        for window in reversed(self.window_history):
            if window["process"] in ("youtube", "vlc", "spotify", "browser"):
                self.last_played_source = window["process"]
                return window
        return None

    def sort_by_time(self) -> list[dict]:
        return sorted(self.window_history, key=lambda x: x["opened_at"])


__all__ = ["AgentContextMemory"]
