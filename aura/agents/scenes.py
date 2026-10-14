"""#132 AgentScenes — готовые сценарии для elder-care.

Наука:
- Nielsen 1993 (recognition over recall) — не надо помнить команды
- Card 1980 (macros) — одна фраза → цепочка действий
- Norman 1988 (composed commands)

Зачем:
  Батя не помнит "включи свет, закрой шторы, выключи музыку".
  Он говорит: "Аура, я спать" — и Aura делает всё сама.
"""
from __future__ import annotations

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent

SCENES: dict[str, list[tuple[str, str]]] = {
    "я спать": [
        ("power", "выключи свет"),
        ("music_local", "выключи музыку"),
        ("security", "проверь двери"),
    ],
    "доброе утро": [
        ("time", "который час"),
        ("music_local", "включи музыку"),
    ],
    "ухожу": [
        ("power", "выключи свет"),
        ("music_local", "выключи музыку"),
        ("security", "проверь двери"),
    ],
    "я дома": [
        ("power", "включи свет"),
    ],
    "болит голова": [
        ("meds", "напомни про таблетки"),
        ("wellness", "стресс"),
    ],
    "тревога": [
        ("sos", "помогите"),
    ],
}


class AgentScenes(BaseAgent):
    """Готовые сценарии — одна фраза → цепочка команд."""

    name = "scenes"

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower().strip()
        return any(scene in t for scene in SCENES)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower().strip()
        for scene_name, commands in SCENES.items():
            if scene_name in t:
                return self._run_scene(scene_name, commands)
        return AgentResponse.not_handled(agent_name=self.name)

    def _run_scene(self, name: str, commands: list[tuple[str, str]]) -> AgentResponse:
        """MVP: возвращаем план сцены (интеграция с orchestrator — завтра)."""
        lines = [f"🎬 Сцена: «{name}»", ""]
        for i, (agent, cmd) in enumerate(commands, 1):
            lines.append(f"  {i}. [{agent}] {cmd}")
        return AgentResponse.ok(
            text="\n".join(lines),
            agent_name=self.name,
        )

    def list_scenes(self) -> str:
        lines = ["🎬 Доступные сцены:"]
        for name in SCENES:
            lines.append(f"  • «{name}»")
        return "\n".join(lines)


__all__ = ["SCENES", "AgentScenes"]
