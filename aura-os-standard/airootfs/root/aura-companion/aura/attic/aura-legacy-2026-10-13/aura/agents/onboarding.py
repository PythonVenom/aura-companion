"""T-user-2 — Onboarding questionnaire.

Наука:
- Schein 2002 — Cold-start: как стартовать без данных
- Beyer & Holtzblatt 1998 — Contextual Inquiry: диалог перед системой
- Nielsen 1993 — Progressive disclosure: пошагово
- Findlater & McGrenere 2004 — Adaptive defaults

При первом запуске — анкета. Aura задаёт вопросы, сохраняет
профиль, и все агенты адаптируются.
"""
from __future__ import annotations

import json
from pathlib import Path

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse

PROFILE_DIR = Path.home() / ".config/aura"
PROFILE_FILE = PROFILE_DIR / "profile.json"


# Вопросы: id, text, type, options (для choice), default
QUESTIONS = [
    {"id": "name", "text": "Как тебя называть?", "type": "text",
     "default": "друг"},
    {"id": "age_group", "text": "Сколько тебе лет?",
     "type": "choice",
     "options": ["<18", "18-40", "40-60", "60-75", "75+"],
     "default": "60-75"},
    {"id": "for_whom", "text": "Для кого Aura?",
     "type": "choice",
     "options": ["себя", "родителя", "ребёнка", "друга"],
     "default": "себя"},
    {"id": "priorities", "text": "Что важнее всего?",
     "type": "multi",
     "options": ["здоровье", "связь", "безопасность",
                 "музыка", "дом", "деньги"],
     "default": ["здоровье", "связь", "безопасность"]},
    {"id": "limitations", "text": "Есть ограничения?",
     "type": "multi",
     "options": ["зрение", "слух", "моторика", "память",
                 "речь", "нет"],
     "default": ["нет"]},
    {"id": "wake_hour", "text": "Во сколько обычно встаёшь?",
     "type": "choice",
     "options": ["до 6", "6-8", "8-10", "10-12", "после 12"],
     "default": "8-10"},
    {"id": "voice_gender", "text": "Какой голос Aura?",
     "type": "choice",
     "options": ["женский", "мужской", "нейтральный"],
     "default": "женский"},
    {"id": "language", "text": "Язык общения?",
     "type": "choice",
     "options": ["ru", "en", "es", "zh", "uk", "kk", "de", "fr"],
     "default": "ru"},
    {"id": "emergency_contact", "text": "Кому звонить в экстренном?",
     "type": "text", "default": ""},
    {"id": "kids_mode", "text": "Режим для детей?",
     "type": "bool", "default": False},
]


class AgentOnboarding(MicroAgent):
    name = "onboarding"

    TRIGGERS = ("анкет", "настрой", "первый запуск", "onboarding",
                "профил", "нача", "setup")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        self._ensure()
        t = request.text.lower()

        if "статус" in t or "сколько" in t:
            return self._status()
        if "начать" in t or "start" in t or "с нуля" in t:
            return self._start()
        if "покажи" in t or "profile" in t or "профиль" in t:
            return self._show_profile()
        if "сброс" in t or "очист" in t:
            return self._reset()

        return AgentResponse.ok(
            text="Onboarding. 'начать анкету' / 'профиль' / 'статус' / 'сброс'",
            agent_name=self.name,
        )

    def _ensure(self) -> None:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> dict:
        if not PROFILE_FILE.exists():
            return {"answers": {}, "current_index": 0, "completed": False}
        try:
            return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"answers": {}, "current_index": 0, "completed": False}

    def _save_state(self, state: dict) -> None:
        PROFILE_FILE.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # --- Публичный API ---

    def get_profile(self) -> dict:
        """Публичный API: текущий профиль для других агентов."""
        return self._load_state().get("answers", {})

    def is_completed(self) -> bool:
        return self._load_state().get("completed", False)

    def reset(self) -> None:
        self._save_state({"answers": {}, "current_index": 0, "completed": False})

    # --- Обработка ---

    def _start(self) -> AgentResponse:
        state = {"answers": {}, "current_index": 0, "completed": False}
        self._save_state(state)
        return self._next_question(state, 0)

    def _next_question(self, state: dict, idx: int) -> AgentResponse:
        if idx >= len(QUESTIONS):
            state["completed"] = True
            self._save_state(state)
            return AgentResponse.ok(
                text="✅ Анкета заполнена. Скажи 'профиль', чтобы увидеть.",
                agent_name=self.name,
            )
        q = QUESTIONS[idx]
        text = f"[{idx+1}/{len(QUESTIONS)}] {q['text']}"
        if q["type"] == "choice":
            text += f"\nВарианты: {', '.join(q['options'])}"
        elif q["type"] == "multi":
            text += f"\nЧерез запятую: {', '.join(q['options'])}"
        text += f"\n(по умолчанию: {q['default']})"
        return AgentResponse.ok(text=text, agent_name=self.name)

    def _status(self) -> AgentResponse:
        state = self._load_state()
        if state.get("completed"):
            return AgentResponse.ok(
                text="✅ Анкета заполнена.", agent_name=self.name,
            )
        idx = state.get("current_index", 0)
        answered = len(state.get("answers", {}))
        return AgentResponse.ok(
            text=f"📝 Отвечено: {answered}/{len(QUESTIONS)}. "
                 f"Текущий: {idx+1}.",
            agent_name=self.name,
        )

    def _show_profile(self) -> AgentResponse:
        state = self._load_state()
        answers = state.get("answers", {})
        if not answers:
            return AgentResponse.ok(
                text="Профиль пуст. Скажи 'начать анкету'.",
                agent_name=self.name,
            )
        lines = ["👤 Профиль:"]
        for k, v in answers.items():
            lines.append(f"  • {k}: {v}")
        done = "✅" if state.get("completed") else "📝"
        lines.append(f"{done} Заполнено: {len(answers)}/{len(QUESTIONS)}")
        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)

    def _reset(self) -> AgentResponse:
        self.reset()
        return AgentResponse.ok(
            text="🗑️ Анкета сброшена.", agent_name=self.name,
        )

    # --- Ответ на вопрос (вызывается из orchestrator) ---

    def answer(self, value: str) -> AgentResponse:
        state = self._load_state()
        idx = state.get("current_index", 0)
        if idx >= len(QUESTIONS):
            return AgentResponse.ok(
                text="Анкета уже заполнена.", agent_name=self.name,
            )
        q = QUESTIONS[idx]
        val = value.strip() or q["default"]
        if q["type"] == "multi" and isinstance(val, str):
            val = [v.strip() for v in val.split(",") if v.strip()]
        elif q["type"] == "bool":
            val = val.lower() in ("да", "yes", "true", "1", "on")
        state["answers"][q["id"]] = val
        state["current_index"] = idx + 1
        self._save_state(state)
        return self._next_question(state, idx + 1)


__all__ = ["AgentOnboarding"]
