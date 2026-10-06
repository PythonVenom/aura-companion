"""T-user-3 — Predictor действий.

Наука:
- Horvitz 1999 — Mixed-initiative: ИИ предлагает, человек решает
- Tennenholtz 2020 — Predictive UX
- Wood & Neal 2007 — Habit loop: trigger → action → reward
- Davenport & Beck 2001 — Attention economics: не отвлекать без нужды

Опирается на routine_learner (T-user-1). Знает паттерны —
предсказывает, что делать сейчас. Никогда не действует сам —
только предлагает.
"""
from __future__ import annotations
from datetime import datetime

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


class AgentPredictor(MicroAgent):
    name = "predictor"

    TRIGGERS = ("что сейчас", "что мне делать", "подскажи", "напомни",
                "что обычно", "предскажи", "прогноз")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()

        if "статус" in t:
            return self._status()
        if "напомни" in t or "подскажи" in t:
            return self._predict_now()
        if "весь день" in t or "прогноз" in t:
            return self._predict_day()

        return AgentResponse.ok(
            text="Предсказатель. 'что сейчас' / 'подскажи' / 'прогноз на день'",
            agent_name=self.name,
        )

    def _routine_agent(self):
        """Получить routine_learner (T-user-1)."""
        try:
            from aura.agents.routine_learner import AgentRoutineLearner
            return AgentRoutineLearner()
        except Exception:
            return None

    def _predict_now(self) -> AgentResponse:
        routine = self._routine_agent()
        if not routine:
            return AgentResponse.ok(
                text="⚠️ Routine learner недоступен.",
                agent_name=self.name,
            )
        predictions = routine.predict()
        if not predictions:
            return AgentResponse.ok(
                text="🤔 Пока не знаю, что ты обычно делаешь в это время. "
                     "Пообщайся со мной побольше.",
                agent_name=self.name,
            )
        # Top-1 (mixed-initiative: одно предложение, не список)
        top = predictions[0]
        pct = int(top["confidence"] * 100)
        return AgentResponse.ok(
            text=f"💡 Похоже, сейчас ты обычно: {top['kind']} — "
                 f"{top['subject']} ({pct}%). Сделать?",
            agent_name=self.name,
        )

    def _predict_day(self) -> AgentResponse:
        routine = self._routine_agent()
        if not routine:
            return AgentResponse.ok(
                text="⚠️ Routine learner недоступен.",
                agent_name=self.name,
            )
        # Симулируем: обходим все часы дня
        all_predictions = []
        for hour in range(24):
            ts = datetime.now().replace(hour=hour, minute=0).timestamp()
            preds = routine.predict(when=ts)
            for p in preds:
                if p["hour"] == hour:
                    all_predictions.append(p)
        if not all_predictions:
            return AgentResponse.ok(
                text="🤔 Паттернов пока нет.",
                agent_name=self.name,
            )
        # Дедупликация по (kind, hour)
        seen = set()
        unique = []
        for p in all_predictions:
            key = (p["kind"], p["hour"])
            if key not in seen:
                seen.add(key)
                unique.append(p)
        unique.sort(key=lambda x: x["hour"])
        lines = ["📅 Прогноз на день:"]
        for p in unique[:10]:
            pct = int(p["confidence"] * 100)
            lines.append(f"  {p['hour']:02d}:00 — {p['kind']}: "
                         f"{p['subject'][:40]} ({pct}%)")
        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)

    def _status(self) -> AgentResponse:
        routine = self._routine_agent()
        if not routine:
            return AgentResponse.ok(
                text="⚠️ Routine learner недоступен.",
                agent_name=self.name,
            )
        s = routine.handle_sync_status() if hasattr(routine, "handle_sync_status") else None
        # Прямой запрос к routine
        try:
            # Быстрый путь — через публичный predict
            n = len(routine.predict())
            return AgentResponse.ok(
                text=f"🤖 Predictor активен. Паттернов в окне ±1ч: {n}.",
                agent_name=self.name,
            )
        except Exception:
            return AgentResponse.ok(
                text="🤖 Predictor активен.",
                agent_name=self.name,
            )

    # --- Публичный API для proactive_alert и др. ---

    def suggest_now(self) -> dict | None:
        """Публичный API: что предложить прямо сейчас (или None)."""
        routine = self._routine_agent()
        if not routine:
            return None
        preds = routine.predict()
        if not preds:
            return None
        return preds[0]


__all__ = ["AgentPredictor"]
