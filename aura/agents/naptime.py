"""#142 AgentNaptime — режим «не беспокоить».

Наука:
- Mycroft Naptime (2018) — DND с таймером
- Nielsen #1 (visibility of status) — юзер видит что DND включён
- Nielsen #3 (user control) — юзер может прервать

Зачем:
  Батя отдыхает → Aura не должна звонить/говорить.
  Proactive не должен пищать. Wellness не напоминает.

Состояние: ~/.config/aura/naptime.json
  {"until": <timestamp>, "reason": "отдых"}
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent

STATE_PATH = Path.home() / ".config/aura/naptime.json"


def is_naptime() -> bool:
    """True если режим «не беспокоить» активен."""
    if not STATE_PATH.exists():
        return False
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        until = float(data.get("until", 0))
        return until > time.time()
    except Exception:
        return False


def _enable(minutes: int, reason: str = "") -> None:
    until = time.time() + minutes * 60
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps({"until": until, "reason": reason}),
        encoding="utf-8",
    )


def _disable() -> None:
    try:
        STATE_PATH.unlink(missing_ok=True)
    except Exception:
        pass


def remaining_min() -> int:
    """Сколько минут осталось (0 если нет)."""
    if not STATE_PATH.exists():
        return 0
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        left = float(data.get("until", 0)) - time.time()
        return max(0, int(left / 60))
    except Exception:
        return 0


class AgentNaptime(BaseAgent):
    """Режим «не беспокоить» с таймером."""

    name = "naptime"

    TRIGGERS = (
        "не беспокоить", "тихий режим", "режим тишины",
        "не мешай", "дай отдохнуть", "я отдыхаю",
        "выйди из тишины", "отключи тишину", "выключи тишину",
        "статус тишины",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()

        if "статус" in t:
            return self._status()

        if any(kw in t for kw in ("выйди", "отключи", "выключи")):
            _disable()
            return AgentResponse.ok("🔔 Тишина выключена", self.name)

        # Парсим минуты: "на 30 минут", "на 1 час"
        minutes = self._parse_minutes(t)
        _enable(minutes)
        if minutes >= 60:
            return AgentResponse.ok(f"🤫 Тишина на {minutes // 60} ч", self.name)
        return AgentResponse.ok(f"🤫 Тишина на {minutes} мин", self.name)

    def _parse_minutes(self, text: str) -> int:
        m = re.search(r"на\s+(\d+)\s*(минут|час)", text)
        if m:
            n = int(m.group(1))
            if "час" in m.group(2):
                return n * 60
            return n
        # Default 30 мин
        return 30

    def _status(self) -> AgentResponse:
        if is_naptime():
            return AgentResponse.ok(
                f"🤫 Тишина активна, осталось {remaining_min()} мин",
                self.name,
            )
        return AgentResponse.ok("🔔 Тишина выключена", self.name)


__all__ = ["STATE_PATH", "AgentNaptime", "is_naptime", "remaining_min"]
