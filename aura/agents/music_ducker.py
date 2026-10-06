"""
Агент приглушения источника (AgentMusicDucker).

Ducking через pactl sink-inputs: снижает громкость всех активных
источников (музыка, браузер, плеер) до 20%. Потом восстанавливает.

Мигрирован из agents/music_ducker.py (монолит, мёртвый по ADR-004).
Изменения:
- Контракт BaseAgent: can_handle / handle
- Логика НЕ менялась
- duck() / un_duck() — публичные (могут звать из главного цикла)

Портирован как заготовка (Фаза 6). НЕ подключён к bootstrap.
См. ADR-004.

ИЗВЕСТНОЕ ОГРАНИЧЕНИЕ:
- Firefox пересоздаёт sink-input при set-sink-input-volume.
  Ducking для Firefox не сработает.
- Работает для VLC, mpv, стабильных плееров.
- Фильтр по application.name — отдельная задача при подключении.
"""

from __future__ import annotations

import subprocess

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentMusicDucker(BaseAgent):
    """Приглушение активных источников звука."""

    name = "music_ducker"

    DUCK_VOLUME = "20%"

    KEYWORDS = (
        "приглуши",
        "восстанови звук",
        "верни звук",
        "тише музыку",
        "громче музыку",
    )

    def __init__(self) -> None:
        self.ready = True
        self.active_sink_inputs: dict[str, int] = {}

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        cmd = request.text.lower()

        if any(kw in cmd for kw in ("восстанови звук", "верни звук", "громче музыку")):
            return AgentResponse.ok(text=self.un_duck(), agent_name=self.name)

        if any(kw in cmd for kw in ("приглуши", "тише музыку")):
            return AgentResponse.ok(text=self.duck(), agent_name=self.name)

        return AgentResponse.not_handled(agent_name=self.name)

    def duck(self) -> str:
        sink_inputs = self._get_all_active_sink_inputs()
        if not sink_inputs:
            return "🔇 Нет активного фонового звука."
        self.active_sink_inputs = {}
        for sid in sink_inputs:
            vol = self._get_sink_input_volume(sid)
            self.active_sink_inputs[sid] = vol
            subprocess.run(
                ["pactl", "set-sink-input-volume", sid, self.DUCK_VOLUME],
                check=False,
            )
        return f"🔉 Приглушила {len(sink_inputs)} источников до 20%."

    def un_duck(self) -> str:
        if not self.active_sink_inputs:
            return "🔇 Нет сохранённых источников для восстановления."
        for sid, vol in self.active_sink_inputs.items():
            try:
                subprocess.run(
                    ["pactl", "set-sink-input-volume", sid, f"{vol}%"],
                    check=False,
                )
            except Exception as e:
                # F-006: не глотать (раздел 17 промта)
                import logging
                logging.getLogger('aura.music_ducker').debug(
                    'music_ducker error: %s', e)
        self.active_sink_inputs = {}
        return "🔊 Восстановила фоновый звук."

    def _get_all_active_sink_inputs(self) -> list[str]:
        try:
            result = subprocess.run(
                ["pactl", "list", "short", "sink-inputs"],
                capture_output=True, text=True, timeout=3,
            )
            streams = []
            for line in result.stdout.split("\\n"):
                if line.strip():
                    parts = line.split()
                    if parts:
                        streams.append(parts[0])
            return streams
        except Exception:
            return []

    def _get_sink_input_volume(self, sink_input_id: str) -> int:
        try:
            result = subprocess.run(
                ["pactl", "get-sink-input-volume", sink_input_id],
                capture_output=True, text=True, timeout=3,
            )
            return int(result.stdout.split()[4].strip("%"))
        except Exception:
            return 100


__all__ = ["AgentMusicDucker"]
