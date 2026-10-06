"""CareAgent — напоминания (еда, вода, сон) — ADR-085."""
from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


CARE_CONFIG = Path.home() / ".cache/aura/care.json"


@dataclass
class CareTask:
    name: str
    times: list = field(default_factory=list)
    message: str = ""
    enabled: bool = True


def should_trigger(task: CareTask, now: datetime) -> bool:
    if not task.enabled:
        return False
    return now.strftime("%H:%M") in task.times


class CareAgent(BaseAgent):
    name = "care"
    MODULE_ALWAYS = True
    KEYWORDS = ("напомни", "напоминания", "пить воду",
                "поесть", "таблетки", "поспать", "забота")

    def __init__(self):
        self.tasks: list = []
        self._load()

    def _load(self):
        if CARE_CONFIG.exists():
            try:
                data = json.loads(CARE_CONFIG.read_text(encoding="utf-8"))
                for t in data.get("tasks", []):
                    self.tasks.append(CareTask(**t))
                return
            except Exception as e:
                # F-006: не глотать (раздел 17 промта)
                import logging
                logging.getLogger('aura.care').debug(
                    'care error: %s', e)
        self.add_task("water", ["10:00","13:00","16:00","19:00"], "Выпей воды")
        self.add_task("food", ["09:00","14:00","19:00"], "Поешь")
        self.add_task("sleep", ["23:00"], "Пора спать")
        self._save()

    def _save(self):
        try:
            CARE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
            CARE_CONFIG.write_text(
                json.dumps({"tasks": [asdict(t) for t in self.tasks]},
                           ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            # F-006: не глотать (раздел 17 промта)
            import logging
            logging.getLogger('aura.care').debug(
                'care error: %s', e)

    def add_task(self, name: str, times: list, message: str):
        self.tasks.append(CareTask(name=name, times=times, message=message))

    def get_due_tasks(self, now: datetime | None = None) -> list:
        now = now or datetime.now()
        return [t for t in self.tasks if should_trigger(t, now)]

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower().strip()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        lines = ["Напоминания:"]
        for t in self.tasks:
            lines.append(f"  - {t.name}: {', '.join(t.times)} — {t.message}")
        return AgentResponse.ok("\n".join(lines), self.name)


__all__ = ["CareAgent", "CareTask", "should_trigger"]
