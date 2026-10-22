"""
Агент фонового анализа (AgentParallelUniverse).

Сканирует открытые окна (wmctrl -l), ищет YouTube/Spotify.
Возвращает insight: «в фоне работает X».

Мигрирован из agents/parallel_universe.py (монолит, мёртвый по ADR-004).
Изменения:
- Контракт BaseAgent: can_handle / handle
- IS_WAYLAND — автоопределение
- Автозапуск в фоне НЕ делаем — только on-demand (start/stop)

Портирован как заготовка (Фаза 6). НЕ подключён к bootstrap.
См. ADR-004.
"""

from __future__ import annotations

import os
import subprocess
import threading
import time

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


def _detect_wayland() -> bool:
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


class AgentParallelUniverse(BaseAgent):
    """Фоновый анализ открытых окон."""

    name = "parallel_universe"

    KEYWORDS = (
        "что в фоне",
        "анализ вкладок",
        "анализ окон",
        "запусти мультивселенную",
        "останови мультивселенную",
    )

    def __init__(self) -> None:
        self.is_wayland = _detect_wayland()
        self.ready = not self.is_wayland
        self.running = False
        self.thread: threading.Thread | None = None
        self.last_analysis: str | None = None
        self._lock = threading.Lock()

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        cmd = request.text.lower()

        if "останови мультивселенную" in cmd:
            return AgentResponse.ok(text=self.stop(), agent_name=self.name)

        if "запусти мультивселенную" in cmd:
            return AgentResponse.ok(text=self.start(), agent_name=self.name)

        if "что в фоне" in cmd or "анализ" in cmd:
            return AgentResponse.ok(text=self.get_insight(), agent_name=self.name)

        return AgentResponse.not_handled(agent_name=self.name)

    def start(self) -> str:
        if self.is_wayland:
            return "⚠️ Недоступно в Wayland"
        if self.running:
            return "⚡ Мультивселенная уже работает"
        self.running = True
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()
        return "⚡ Мультивселенная запущена. Аура анализирует всё в фоне."

    def stop(self) -> str:
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=2.0)
            self.thread = None
        return "⏹️ Мультивселенная остановлена"

    def get_insight(self) -> str:
        if self.is_wayland:
            return "⚠️ Недоступно в Wayland"
        result = self._analyze_tabs()
        return result or "🧠 Мультивселенная думает..."

    def _monitor(self) -> None:
        while self.running:
            self._analyze_tabs()
            time.sleep(5)

    def _analyze_tabs(self) -> str | None:
        try:
            result = subprocess.run(
                ["wmctrl", "-l"], capture_output=True, text=True, timeout=3,
            )
            for line in result.stdout.split("\\n"):
                if not line.strip():
                    continue
                parts = line.split(None, 4)
                if len(parts) < 5:
                    continue
                title = parts[4]
                if "youtube" in title.lower() or "spotify" in title.lower():
                    with self._lock:
                        self.last_analysis = f"🎵 В фоне работает: {title[:40]}"
                    return self.last_analysis
            with self._lock:
                self.last_analysis = "📊 Медиа в фоне не найдено"
            return self.last_analysis
        except Exception:
            return "⚠️ Не смогла проанализировать вкладки"


__all__ = ["AgentParallelUniverse"]
