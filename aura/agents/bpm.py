"""BPM метроном (ADR-044 шаг 7).

Только расчёт: BPM -> интервал в мс. Звук воспроизводит speaker
или внешний процесс по запросу.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


@dataclass
class Beat:
    bpm: int
    interval_ms: int


def bpm_to_interval(bpm: int) -> int:
    """BPM -> интервал в миллисекундах."""
    if bpm <= 0:
        raise ValueError("BPM должен быть > 0")
    if bpm > 400:
        raise ValueError("BPM > 400 — нереально быстро")
    return int(60000 / bpm)


class AgentBPM(BaseAgent):
    """Метроном по BPM.

    Команды:
      - «метроном 120»
      - «bpm 90»
      - «какой темп 4/4»
    """

    name = "bpm"
    MODULE_ALWAYS = True
    KEYWORDS = ("метроном", "bpm", "темп 4/4", "какой темп")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        # Парсим BPM
        m = re.search(r"(\d{2,3})", text)
        if not m:
            return AgentResponse.ok("Скажи: «метроном 120»", self.name)

        bpm = int(m.group(1))
        try:
            interval = bpm_to_interval(bpm)
        except ValueError as e:
            return AgentResponse.ok(f"❌ {e}", self.name)

        # Категория темпа
        if bpm < 60:
            cat = "Largo (медленно)"
        elif bpm < 90:
            cat = "Andante (шагом)"
        elif bpm < 120:
            cat = "Moderato (умеренно)"
        elif bpm < 168:
            cat = "Allegro (быстро)"
        else:
            cat = "Presto (очень быстро)"

        return AgentResponse.ok(
            f"🥁 {bpm} BPM = {interval} мс/удар. {cat}", self.name
        )


__all__ = ["AgentBPM", "bpm_to_interval", "Beat"]
