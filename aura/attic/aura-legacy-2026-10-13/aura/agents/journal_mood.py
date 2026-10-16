"""VoiceJournal — дневник настроения (ADR-086)."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent

DEFAULT_ROOT = Path.home() / ".cache/aura/journal"

POSITIVE = {"отлично","хорошо","супер","класс","бодро","заряжен","спокоен","радостно"}
NEGATIVE = {"плохо","паршиво","ужасно","тяжело","грустно","тревожно","устал","разбит"}


def parse_mood(text: str) -> int | None:
    t = text.lower()
    # Число: "настроение 7", "7 из 10"
    m = re.search(r"\b(\d{1,2})\b", t)
    if m:
        n = int(m.group(1))
        if 0 <= n <= 10:
            return n
    # Слова
    for w in POSITIVE:
        if w in t:
            return 8
    for w in NEGATIVE:
        if w in t:
            return 3
    return None


class VoiceJournal(BaseAgent):
    name = "journal_mood"
    MODULE_ALWAYS = True
    KEYWORDS = ("дневник", "настроение", "занеси", "как я себя",
                "как настроение", "запиши")

    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else DEFAULT_ROOT
        self.root.mkdir(parents=True, exist_ok=True)
        self._file = self.root / "mood.jsonl"

    def add(self, text: str, mood: int | None = None):
        if mood is None:
            mood = parse_mood(text)
        entry = {"text": text, "mood": mood, "ts": time.time()}
        with open(self._file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def read_all(self) -> list:
        if not self._file.exists():
            return []
        out = []
        for line in self._file.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except Exception:
                continue
        return out

    def stats_last_days(self, days: int = 7) -> dict:
        cutoff = time.time() - days * 86400
        entries = [e for e in self.read_all() if e.get("ts", 0) >= cutoff]
        moods = [e["mood"] for e in entries if e.get("mood") is not None]
        return {
            "count": len(entries),
            "avg": round(sum(moods) / len(moods), 1) if moods else None,
            "min": min(moods) if moods else None,
            "max": max(moods) if moods else None,
        }

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower().strip()
        if "дневник" in text or "как я себя" in text or "как настроение" in text:
            return True
        if "занеси" in text or "запиши" in text:
            if parse_mood(text) is not None or "настроение" in text:
                return True
        return False

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        text = request.text.lower()
        # Запрос статистики
        if "как я себя" in text or "как настроение" in text or "статистика" in text:
            s = self.stats_last_days(7)
            if s["count"] == 0:
                return AgentResponse.ok("Дневник пуст.", self.name)
            return AgentResponse.ok(
                f"За 7 дней: {s['count']} записей, "
                f"среднее {s['avg']}, мин {s['min']}, макс {s['max']}",
                self.name,
            )
        # Запись
        mood = parse_mood(text)
        self.add(text, mood)
        return AgentResponse.ok(
            f"Записала: настроение {mood if mood is not None else '?'}",
            self.name,
        )


__all__ = ["DEFAULT_ROOT", "VoiceJournal", "parse_mood"]
