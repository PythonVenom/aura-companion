"""T051 — поговорить по душам.

Наука:
- Active Listening (Carl Rogers, 1957)
- Empathic Dialogue — отражение чувств, не решение проблем
- Контекст: T052 emotion_voice + journal + время суток
"""
from __future__ import annotations
import sqlite3
import time
from pathlib import Path

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


JOURNAL_DB = Path.home() / ".local/share/aura/journal.db"


TRIGGERS = (
    "поговорить по душам", "поговорим", "тяжело", "мне плохо",
    "мне грустно", "одиноко", "устал от всего", "не могу больше",
    "поговори со мной", "выслушай меня",
)

# Rogers 1957 — Active Listening prompts
EMPATHIC_PROMPTS = {
    "night": "Сейчас ночь. Ты рядом. Не спеши. Слушай больше, чем говори.",
    "day": "Слушай. Отражай чувства. Не давай советов, если не просят.",
    "evening": "Вечер. Мягко. Не торопи. Дай выговориться.",
}


class AgentSoulTalk(MicroAgent):
    name = "soul_talk"

    TRIGGERS = TRIGGERS

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()
        if "статус" in t:
            return self._status()
        # Всё остальное — эмпатичный ответ
        return await self._soul_talk(request.text)

    def _status(self) -> AgentResponse:
        return AgentResponse.ok(
            text="💬 Режим «по душам» готов. Скажи что на душе.",
            agent_name=self.name,
        )

    def _time_of_day(self) -> str:
        h = time.localtime().tm_hour
        if 5 <= h < 12:
            return "day"
        if 12 <= h < 18:
            return "day"
        if 18 <= h < 23:
            return "evening"
        return "night"

    def _recent_journal(self, n: int = 3) -> list[str]:
        if not JOURNAL_DB.exists():
            return []
        try:
            conn = sqlite3.connect(JOURNAL_DB)
            rows = conn.execute(
                "SELECT text FROM entries ORDER BY id DESC LIMIT ?", (n,)
            ).fetchall()
            conn.close()
            return [r[0][:100] for r in rows]
        except Exception:
            return []

    def _recent_emotion(self) -> str | None:
        p = Path.home() / ".local/share/aura/proactive.db"
        if not p.exists():
            return None
        try:
            conn = sqlite3.connect(p)
            row = conn.execute(
                "SELECT val FROM state WHERE key='last_emotion'"
            ).fetchone()
            conn.close()
            if row:
                return row[0].strip('"')
        except Exception:
            return None
        return None

    def _build_context(self) -> str:
        parts = [EMPATHIC_PROMPTS[self._time_of_day()]]
        emo = self._recent_emotion()
        if emo:
            parts.append(f"Последняя эмоция по голосу: {emo}.")
        journal = self._recent_journal(3)
        if journal:
            parts.append("Последние записи журнала:")
            for j in journal:
                parts.append(f"  — {j}")
        return "\n".join(parts)

    async def _soul_talk(self, text: str) -> AgentResponse:
        context = self._build_context()

        # Пробуем отдать в LLM (brain)
        try:
            from aura.core.brain import Brain  # type: ignore
            brain = Brain()
            prompt = (
                "Ты — Aura, локальный голосовой помощник для пожилого человека. "
                "Ты сейчас в режиме «поговорить по душам». "
                "Принципы: Active Listening (Rogers 1957), отражение чувств, "
                "никаких советов без просьбы. Отвечай коротко (2–3 фразы). "
                "Эмпатия важнее информации.\n\n"
                f"Контекст:\n{context}\n\n"
                f"Человек говорит: {text}"
            )
            reply = await brain.ask(prompt)
            if reply:
                return AgentResponse.ok(text=reply, agent_name=self.name)
        except Exception as e:
            # F-006: не глотать (раздел 17 промта)
            import logging
            logging.getLogger('aura.soul_talk').debug(
                'soul_talk error: %s', e)

        # Fallback — если LLM недоступен
        return AgentResponse.ok(
            text=(
                "Я рядом. Слушаю. "
                "Расскажи, что на душе — не спеши, я не тороплю."
            ),
            agent_name=self.name,
        )
