"""T-user-1 — Routine learner (паттерны распорядка).

Наука:
- Lane 2011 — Behavior mining (passive sensing)
- Horvitz 1999 — Mixed-initiative UI
- Srinivasan 2019 — Routine detection из временных рядов
- Wood & Neal 2007 — Habit formation (21+ день)

Идея: пассивно наблюдать события из health_twin (время вставания,
лекарства, диалоги). Строить паттерны: "в 10:00 обычно встаёт",
"после завтрака принимает таблетки". Проактивно напоминать.
"""
from __future__ import annotations

import sqlite3
import time
from datetime import datetime
from pathlib import Path

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse

TWIN_DB = Path.home() / ".local/share/aura/health_twin.db"
ROUTINE_DB = Path.home() / ".local/share/aura/routine.db"

LEARN_WINDOW_DAYS = 30
MIN_OBSERVATIONS = 5
CONFIDENCE_THRESHOLD = 0.6


class AgentRoutineLearner(MicroAgent):
    name = "routine_learner"

    TRIGGERS = ("распорядок", "привычк", "рутин", "обычно", "всегда делаю",
                "что я обычно", "мой день", "routine")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        self._ensure()
        t = request.text.lower()

        if "статус" in t or "сколько" in t:
            return self._status()
        if "покажи" in t or "какой" in t or "мой день" in t:
            return self._show_routines()
        if "обнови" in t or "пересчитай" in t or "изучи" in t:
            return self._learn()
        if "очист" in t or "сброс" in t:
            return self._clear()

        return AgentResponse.ok(
            text="Распорядок. 'покажи' / 'обнови' / 'статус' / 'очисти'",
            agent_name=self.name,
        )

    def _ensure(self) -> None:
        ROUTINE_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(ROUTINE_DB)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS routines (
                id INTEGER PRIMARY KEY,
                kind TEXT NOT NULL,
                subject TEXT NOT NULL,
                hour_bucket INTEGER NOT NULL,
                confidence REAL NOT NULL,
                observations INTEGER NOT NULL,
                learned_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_routine_unique
            ON routines(kind, subject, hour_bucket)
        """)
        conn.commit()
        conn.close()

    def observe(self, kind: str, subject: str, ts: float | None = None) -> None:
        """Публичный API: записать наблюдение (вызывают другие агенты)."""
        self._ensure()
        from aura.agents.health_twin import AgentHealthTwin
        twin = AgentHealthTwin()
        twin.add_event(kind=kind, subject=subject, payload={"text": subject}, ts=ts)

    def _learn(self) -> AgentResponse:
        if not TWIN_DB.exists():
            return AgentResponse.ok(
                text="📊 Нет данных для обучения. Пообщайся с Aura.",
                agent_name=self.name,
            )

        since = time.time() - LEARN_WINDOW_DAYS * 86400
        conn = sqlite3.connect(TWIN_DB)
        rows = conn.execute(
            "SELECT kind, subject, ts FROM events WHERE ts >= ?",
            (since,),
        ).fetchall()
        conn.close()

        if len(rows) < MIN_OBSERVATIONS:
            return AgentResponse.ok(
                text=f"📊 Мало данных ({len(rows)}<{MIN_OBSERVATIONS}).",
                agent_name=self.name,
            )

        from collections import defaultdict
        buckets: dict[tuple[str, str, int], list[float]] = defaultdict(list)
        for kind, subject, ts in rows:
            hour = datetime.fromtimestamp(ts).hour
            key = (kind, subject[:50], hour)
            buckets[key].append(ts)

        learned = 0
        conn = sqlite3.connect(ROUTINE_DB)
        conn.execute("DELETE FROM routines")
        for (kind, subject, hour), timestamps in buckets.items():
            n = len(timestamps)
            if n < MIN_OBSERVATIONS:
                continue
            days_observed = {datetime.fromtimestamp(t).date() for t in timestamps}
            confidence = len(days_observed) / LEARN_WINDOW_DAYS
            if confidence < CONFIDENCE_THRESHOLD:
                continue
            conn.execute("""
                INSERT INTO routines (kind, subject, hour_bucket, confidence,
                                       observations, learned_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (kind, subject, hour, confidence, n, time.time()))
            learned += 1
        conn.commit()
        conn.close()

        return AgentResponse.ok(
            text=f"📊 Изучено {learned} паттернов за {LEARN_WINDOW_DAYS} дней.",
            agent_name=self.name,
        )

    def _show_routines(self) -> AgentResponse:
        conn = sqlite3.connect(ROUTINE_DB)
        rows = conn.execute("""
            SELECT kind, subject, hour_bucket, confidence, observations
            FROM routines ORDER BY hour_bucket, kind
        """).fetchall()
        conn.close()
        if not rows:
            return AgentResponse.ok(
                text="📊 Паттернов пока нет. Скажи 'обнови распорядок'.",
                agent_name=self.name,
            )
        lines = ["📅 Распорядок:"]
        for kind, subject, hour, conf, n in rows:
            pct = int(conf * 100)
            lines.append(f"  {hour:02d}:00 — {kind}: {subject[:40]} ({pct}%, {n}×)")
        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)

    def _status(self) -> AgentResponse:
        conn = sqlite3.connect(ROUTINE_DB)
        n = conn.execute("SELECT COUNT(*) FROM routines").fetchone()[0]
        conn.close()
        twin_size = 0
        if TWIN_DB.exists():
            conn = sqlite3.connect(TWIN_DB)
            twin_size = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            conn.close()
        return AgentResponse.ok(
            text=f"📊 Паттернов: {n}. Событий в двойнике: {twin_size}.",
            agent_name=self.name,
        )

    def _clear(self) -> AgentResponse:
        conn = sqlite3.connect(ROUTINE_DB)
        n = conn.execute("DELETE FROM routines").rowcount
        conn.commit()
        conn.close()
        return AgentResponse.ok(
            text=f"🗑️ Удалено {n} паттернов.", agent_name=self.name,
        )

    def predict(self, when: float | None = None) -> list[dict]:
        """Публичный API: что ожидается в указанное время (±1 час)."""
        if not ROUTINE_DB.exists():
            return []
        now = datetime.fromtimestamp(when or time.time())
        conn = sqlite3.connect(ROUTINE_DB)
        rows = conn.execute("""
            SELECT kind, subject, hour_bucket, confidence
            FROM routines
            WHERE hour_bucket BETWEEN ? AND ?
            ORDER BY confidence DESC
        """, ((now.hour - 1) % 24, (now.hour + 1) % 24)).fetchall()
        conn.close()
        return [
            {"kind": k, "subject": s, "hour": h, "confidence": c}
            for k, s, h, c in rows
        ]


__all__ = ["AgentRoutineLearner"]
