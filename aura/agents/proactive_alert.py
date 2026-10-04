"""T054 — proactive тревога. Если тишина N часов — сигнал семье.

Наука:
- Inactivity Detection (Kasteren 2011, Activity Recognition)
- Escalation Protocol: silence → notify → escalate
- State: last interaction timestamp в SQLite
"""
from __future__ import annotations
import json
import sqlite3
import time
from pathlib import Path

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


STATE_DB = Path.home() / ".local/share/aura/proactive.db"
DEFAULT_THRESHOLD_HOURS = 6.0


class AgentProactiveAlert(MicroAgent):
    name = "proactive_alert"

    TRIGGERS = ("тревога", "проверь батю", "молчит", "proactive",
                "если я не отвечаю", "sos по тишине")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        self._ensure()
        t = request.text.lower()
        if "статус" in t or "сколько" in t:
            return self._status()
        if "порог" in t or "часов" in t:
            return self._set_threshold(request.text)
        if "сбрось" in t or "проверил" in t:
            return self._touch()
        return AgentResponse.ok(
            text=f"Тревога по тишине. Порог: {self._threshold():.1f}ч. "
                 f"Последний контакт: {self._since_last():.1f}ч назад.",
            agent_name=self.name,
        )

    def _ensure(self) -> None:
        STATE_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(STATE_DB)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS state (
                key TEXT PRIMARY KEY,
                val TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def _get(self, key: str, default=None):
        conn = sqlite3.connect(STATE_DB)
        row = conn.execute("SELECT val FROM state WHERE key=?", (key,)).fetchone()
        conn.close()
        if not row:
            return default
        try:
            return json.loads(row[0])
        except Exception:
            return row[0]

    def _set(self, key: str, val) -> None:
        conn = sqlite3.connect(STATE_DB)
        conn.execute(
            "INSERT OR REPLACE INTO state (key, val) VALUES (?, ?)",
            (key, json.dumps(val, ensure_ascii=False)),
        )
        conn.commit()
        conn.close()

    def _threshold(self) -> float:
        v = self._get("threshold_hours", DEFAULT_THRESHOLD_HOURS)
        try:
            return float(v)
        except Exception:
            return DEFAULT_THRESHOLD_HOURS

    def _last_ts(self) -> float:
        v = self._get("last_interaction_ts")
        if v is None:
            self._set("last_interaction_ts", time.time())
            return time.time()
        try:
            return float(v)
        except Exception:
            return time.time()

    def _since_last(self) -> float:
        return (time.time() - self._last_ts()) / 3600.0

    def touch(self) -> None:
        """Публичный API: обновить timestamp (вызывает orchestrator)."""
        self._set("last_interaction_ts", time.time())

    def _touch(self) -> AgentResponse:
        self.touch()
        return AgentResponse.ok(
            text="✅ Тревога сброшена. Считаю заново.",
            agent_name=self.name,
        )

    def _set_threshold(self, text: str) -> AgentResponse:
        import re
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*час", text.lower())
        if not m:
            return AgentResponse.ok(
                text="Формат: 'порог тревоги 6 часов'",
                agent_name=self.name,
            )
        hours = float(m.group(1).replace(",", "."))
        self._set("threshold_hours", hours)
        return AgentResponse.ok(
            text=f"✅ Порог тревоги: {hours:.1f}ч.",
            agent_name=self.name,
        )

    def _status(self) -> AgentResponse:
        since = self._since_last()
        threshold = self._threshold()
        state = "🔴 ТРЕВОГА" if since >= threshold else "🟢 ОК"
        return AgentResponse.ok(
            text=f"{state}: тишина {since:.1f}ч / порог {threshold:.1f}ч.",
            agent_name=self.name,
        )

    def check(self) -> bool:
        """Публичный API: проверить, нужна ли эскалация. True = тревога."""
        if self._since_last() >= self._threshold():
            if not self._get("alert_active", False):
                self._set("alert_active", True)
                return True
        return False

    def clear_alert(self) -> None:
        self._set("alert_active", False)
