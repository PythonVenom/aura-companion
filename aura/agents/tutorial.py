"""Tutorial agent — 5 уроков для бати (F-036).

Наука (Д4):
- Fogg 2009 — Tiny Habits: маленькие шаги
- Nielsen 1993 — Progressive disclosure
- Csikszentmihalyi 1990 — Flow: баланс сложности
- Krug 2014 — Don't Make Me Think
- Bloom 1984 — Mastery learning
"""
from __future__ import annotations

import json
from pathlib import Path

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse

STATE_FILE = Path.home() / ".config" / "aura" / "tutorial_state.json"


# 5 уроков: id, что сказать, что ожидать, подсказка
LESSONS = [
    {
        "id": 1,
        "title": "Как вызвать Ауру",
        "say": "Аура, привет",
        "expect": "Аура отвечает",
        "hint": "Скажи: 'Аура', пауза, 'привет'",
    },
    {
        "id": 2,
        "title": "Время и погода",
        "say": "Аура, сколько времени",
        "expect": "Аура говорит время",
        "hint": "Попробуй: 'Аура, какая погода'",
    },
    {
        "id": 3,
        "title": "Таблетки",
        "say": "Аура, напомни выпить таблетки в 9",
        "expect": "Аура создаёт напоминание",
        "hint": "Говори время чётко: 'в 9 утра'",
    },
    {
        "id": 4,
        "title": "Позвонить близким",
        "say": "Аура, позвони сыну",
        "expect": "Аура звонит контакту",
        "hint": "Сначала добавь контакт: 'Аура, установи контакт сын +7999...'",
    },
    {
        "id": 5,
        "title": "SOS",
        "say": "Аура, помоги",
        "expect": "Аура зовёт помощь",
        "hint": "Если плохо — просто скажи 'SOS'",
    },
]


class AgentTutorial(MicroAgent):
    name = "tutorial"

    TRIGGERS = ("туториал", "обучен", "научи", "урок", "tutorial")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()

        if "начать" in t or "start" in t or "с нуля" in t:
            return self._start()
        if "статус" in t or "сколько" in t:
            return self._status()
        if "дальше" in t or "next" in t:
            return self._next()
        if "сброс" in t:
            return self._reset()

        return AgentResponse.ok(
            text="Туториал. 'начать' / 'дальше' / 'статус' / 'сброс'",
            agent_name=self.name,
        )

    def _load(self) -> dict:
        if not STATE_FILE.exists():
            return {"current": 0, "completed": []}
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"current": 0, "completed": []}

    def _save(self, state: dict) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _start(self) -> AgentResponse:
        state = {"current": 0, "completed": []}
        self._save(state)
        return self._lesson_response(0)

    def _next(self) -> AgentResponse:
        state = self._load()
        idx = state.get("current", 0)
        if idx not in state.get("completed", []):
            state.setdefault("completed", []).append(idx)
        idx += 1
        state["current"] = idx
        self._save(state)
        if idx >= len(LESSONS):
            return AgentResponse.ok(
                text="🏆 Туториал пройден! Ты освоил 5 команд. "
                     "Теперь говори с Аурой свободно.",
                agent_name=self.name,
            )
        return self._lesson_response(idx)

    def _lesson_response(self, idx: int) -> AgentResponse:
        l = LESSONS[idx]
        text = (
            f"📚 Урок {l['id']}/5: {l['title']}\n"
            f"Скажи: «{l['say']}»\n"
            f"Ожидай: {l['expect']}\n"
            f"Подсказка: {l['hint']}\n"
            f"Скажи 'дальше' когда готов."
        )
        return AgentResponse.ok(text=text, agent_name=self.name)

    def _status(self) -> AgentResponse:
        state = self._load()
        done = len(state.get("completed", []))
        return AgentResponse.ok(
            text=f"📊 Туториал: {done}/{len(LESSONS)} уроков пройдено.",
            agent_name=self.name,
        )

    def _reset(self) -> AgentResponse:
        self._save({"current": 0, "completed": []})
        return AgentResponse.ok(text="🗑️ Туториал сброшен.", agent_name=self.name)


__all__ = ["AgentTutorial", "LESSONS"]
