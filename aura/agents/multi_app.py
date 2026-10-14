"""#149 MultiAppAutomation — цепочки между приложениями.

Наука:
- Macro (Card 1980) — одна команда = много действий
- Workflow Automation (van der Aalst 2016) — оркестрация приложений
- Composed Command (Norman 1988)

Зачем:
  «Аура, режим работы» → открыть VSCode, Firefox, включить lo-fi
  «Аура, режим кино» → закрыть браузер, открыть VLC, потушить свет

Сценарии: ~/.config/aura/multi_app.json
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent
from aura.core.recall_log import record

SCENARIOS_PATH = Path.home() / ".config/aura/multi_app.json"


@dataclass
class Step:
    agent: str
    action: str
    args: dict = field(default_factory=dict)


@dataclass
class Scenario:
    name: str
    triggers: list[str]
    steps: list[Step]


def _default_scenarios() -> list[Scenario]:
    return [
        Scenario(
            name="работа",
            triggers=["режим работы", "рабочий режим"],
            steps=[
                Step("app_launcher", "open", {"name": "code"}),
                Step("browser_tabs", "new", {"url": "about:blank"}),
                Step("music_local", "play", {}),
            ],
        ),
        Scenario(
            name="кино",
            triggers=["режим кино", "смотреть фильм"],
            steps=[
                Step("browser_tabs", "close_all", {}),
                Step("media_search", "open", {"query": "фильм"}),
            ],
        ),
        Scenario(
            name="отдых",
            triggers=["режим отдыха", "отдохнуть"],
            steps=[
                Step("scenes", "run", {"name": "я спать"}),
                Step("naptime", "enable", {"minutes": 30}),
            ],
        ),
        Scenario(
            name="уборка",
            triggers=["режим уборки", "уборка"],
            steps=[
                Step("music_local", "play", {}),
                Step("scenes", "run", {"name": "я дома"}),
            ],
        ),
    ]


def load_scenarios() -> list[Scenario]:
    if not SCENARIOS_PATH.exists():
        return _default_scenarios()
    try:
        data = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
        return [
            Scenario(
                name=s["name"],
                triggers=s["triggers"],
                steps=[Step(**step) for step in s["steps"]],
            )
            for s in data.get("scenarios", [])
        ]
    except Exception:
        return _default_scenarios()


def save_scenarios(scenarios: list[Scenario]) -> None:
    SCENARIOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCENARIOS_PATH.write_text(
        json.dumps(
            {"scenarios": [
                {
                    "name": s.name,
                    "triggers": s.triggers,
                    "steps": [asdict(step) for step in s.steps],
                }
                for s in scenarios
            ]},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )


class AgentMultiApp(BaseAgent):
    """Цепочки между приложениями."""

    name = "multi_app"

    TRIGGERS = (
        "режим работы", "рабочий режим",
        "режим кино", "смотреть фильм",
        "режим отдыха", "отдохнуть",
        "режим уборки", "уборка",
        "цепочка", "сценарий", "комбо",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()
        scenarios = load_scenarios()

        # Найти сценарий
        for s in scenarios:
            if any(trig in t for trig in s.triggers):
                return self._run_scenario(s)

        # Список
        lines = ["🎬 Сценарии:"]
        for s in scenarios:
            lines.append(f"  • {s.name} — триггеры: {', '.join(s.triggers[:2])}")
        return AgentResponse.ok("\n".join(lines), self.name)

    def _run_scenario(self, scenario: Scenario) -> AgentResponse:
        """MVP: показать план + записать в recall."""
        lines = [f"🎬 Сценарий «{scenario.name}»", ""]
        for i, step in enumerate(scenario.steps, 1):
            args = ", ".join(f"{k}={v}" for k, v in step.args.items())
            lines.append(f"  {i}. [{step.agent}] {step.action} ({args})")

        try:
            record(
                self.name,
                "scenario_run",
                f"{scenario.name} → {len(scenario.steps)} шагов",
            )
        except Exception:
            pass

        return AgentResponse.ok("\n".join(lines), self.name)

    def list_scenarios(self) -> str:
        scenarios = load_scenarios()
        lines = [f"🎬 Доступные сценарии ({len(scenarios)}):"]
        for s in scenarios:
            lines.append(f"  • {s.name}: {', '.join(s.triggers)}")
        return "\n".join(lines)


__all__ = [
    "SCENARIOS_PATH",
    "AgentMultiApp",
    "Scenario",
    "Step",
    "load_scenarios",
    "save_scenarios",
]
