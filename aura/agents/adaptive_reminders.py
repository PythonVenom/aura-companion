"""T-user-4 — Adaptive reminders.

Наука:
- Horvitz 1999 — Mixed-initiative, время напоминания = динамическое
- Iqbal & Horvitz 2010 — Не прерывать в неподходящий момент
- Dey 2001 — Context-aware computing
- Wood & Neal 2007 — Habit loop

Отличие от статичных напоминаний:
- Время сдвигается по факту (если батя пьёт таблетки в 10:20, не 10:00)
- Способ адаптируется (голос / уведомление / эскалация семье)
- Учитывает паттерны из routine_learner
"""
from __future__ import annotations
import sqlite3
import time
from pathlib import Path
from datetime import datetime

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


REMINDERS_DB = Path.home() / ".local/share/aura/reminders.db"
TWIN_DB = Path.home() / ".local/share/aura/health_twin.db"

# Окно сдвига: если факт отличается от запланированного ≤ 90 мин —
# считаем это тем же напоминанием и сдвигаем «виртуальное» время
DRIFT_WINDOW_MIN = 90
MIN_SAMPLES_FOR_ADAPT = 3


class AgentAdaptiveReminders(MicroAgent):
    name = "adaptive_reminders"

    TRIGGERS = ("напоминание", "напомни", "лекарств", "таблетк",
                "адаптив", "сдвинь", "пропустил")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        self._ensure()
        t = request.text.lower()

        if "статус" in t or "список" in t:
            return self._status()
        if "добавь" in t or "создай" in t:
            return self._add(request.text)
        if "принял" in t or "выпил" in t or "сделал" in t:
            return self._confirm(request.text)
        if "пропустил" in t or "забудь" in t:
            return self._skip(request.text)

        return AgentResponse.ok(
            text="Адаптивные напоминания. 'добавь <что> в <время>' / "
                 "'принял <что>' / 'статус'",
            agent_name=self.name,
        )

    def _ensure(self) -> None:
        REMINDERS_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(REMINDERS_DB)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY,
                what TEXT NOT NULL,
                scheduled_hhmm TEXT NOT NULL,
                effective_hhmm TEXT,
                created_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY,
                reminder_id INTEGER NOT NULL,
                fact_ts REAL NOT NULL,
                action TEXT NOT NULL,
                FOREIGN KEY (reminder_id) REFERENCES reminders(id)
            )
        """)
        conn.commit()
        conn.close()

    # --- Публичный API ---

    def add(self, what: str, scheduled_hhmm: str) -> int:
        self._ensure()
        conn = sqlite3.connect(REMINDERS_DB)
        cur = conn.execute("""
            INSERT INTO reminders (what, scheduled_hhmm, created_at)
            VALUES (?, ?, ?)
        """, (what, scheduled_hhmm, time.time()))
        rid = cur.lastrowid
        conn.commit()
        conn.close()
        return rid

    def record_fact(self, what: str, action: str = "taken",
                    ts: float | None = None) -> bool:
        """Публичный API: зафиксировать факт (принял / пропустил)."""
        self._ensure()
        conn = sqlite3.connect(REMINDERS_DB)
        row = conn.execute(
            "SELECT id, scheduled_hhmm FROM reminders WHERE what LIKE ? "
            "ORDER BY id DESC LIMIT 1",
            (f"%{what}%",),
        ).fetchone()
        if not row:
            conn.close()
            return False
        rid, _ = row
        conn.execute("""
            INSERT INTO facts (reminder_id, fact_ts, action)
            VALUES (?, ?, ?)
        """, (rid, ts or time.time(), action))
        conn.commit()
        conn.close()
        return True

    def adapted_time(self, reminder_id: int) -> str | None:
        """Средний факт по последним N наблюдениям → новое время."""
        conn = sqlite3.connect(REMINDERS_DB)
        rows = conn.execute("""
            SELECT fact_ts FROM facts
            WHERE reminder_id = ? AND action = 'taken'
            ORDER BY fact_ts DESC LIMIT ?
        """, (reminder_id, MIN_SAMPLES_FOR_ADAPT * 2)).fetchall()
        conn.close()
        if len(rows) < MIN_SAMPLES_FOR_ADAPT:
            return None
        # Среднее HH:MM
        minutes = []
        for (ts,) in rows:
            dt = datetime.fromtimestamp(ts)
            minutes.append(dt.hour * 60 + dt.minute)
        avg = sum(minutes) // len(minutes)
        return f"{avg // 60:02d}:{avg % 60:02d}"

    # --- Обработка из handle ---

    def _add(self, text: str) -> AgentResponse:
        import re
        m = re.search(
            r"добав[ьи]\s+(.+?)\s+в\s+(\d{1,2}[:.]\d{2})",
            text.lower(),
        )
        if not m:
            return AgentResponse.ok(
                text="Формат: 'добавь лекарство X в 10:00'",
                agent_name=self.name,
            )
        what = m.group(1).strip()
        hhmm = m.group(2).replace(".", ":")
        hh, mm = hhmm.split(":")
        hhmm = f"{int(hh):02d}:{mm}"
        rid = self.add(what, hhmm)
        return AgentResponse.ok(
            text=f"⏰ Напоминание #{rid}: {what} в {hhmm}",
            agent_name=self.name,
        )

    def _confirm(self, text: str) -> AgentResponse:
        import re
        m = re.search(r"(?:принял|выпил|сделал)\s+(.+)", text.lower())
        if not m:
            return AgentResponse.ok(
                text="Формат: 'принял лекарство X'",
                agent_name=self.name,
            )
        what = m.group(1).strip()
        if self.record_fact(what, "taken"):
            # Проверим, не сдвинулось ли время
            conn = sqlite3.connect(REMINDERS_DB)
            row = conn.execute(
                "SELECT id, scheduled_hhmm FROM reminders "
                "WHERE what LIKE ? ORDER BY id DESC LIMIT 1",
                (f"%{what}%",),
            ).fetchone()
            conn.close()
            if row:
                rid, scheduled = row
                adapted = self.adapted_time(rid)
                if adapted and adapted != scheduled:
                    return AgentResponse.ok(
                        text=f"✅ Принято. Замечаю: обычно в {adapted}, "
                             f"а не в {scheduled}. Сдвинуть?",
                        agent_name=self.name,
                    )
            return AgentResponse.ok(
                text=f"✅ Отмечено: {what}", agent_name=self.name,
            )
        return AgentResponse.ok(
            text=f"⚠️ Не нашла напоминание '{what}'",
            agent_name=self.name,
        )

    def _skip(self, text: str) -> AgentResponse:
        import re
        m = re.search(r"(?:пропустил|забудь)\s+(.+)", text.lower())
        if not m:
            return AgentResponse.ok(
                text="Формат: 'пропустил лекарство X'",
                agent_name=self.name,
            )
        what = m.group(1).strip()
        self.record_fact(what, "skipped")
        return AgentResponse.ok(
            text=f"📝 Отмечено как пропущено: {what}",
            agent_name=self.name,
        )

    def _status(self) -> AgentResponse:
        conn = sqlite3.connect(REMINDERS_DB)
        rows = conn.execute("""
            SELECT id, what, scheduled_hhmm FROM reminders ORDER BY id
        """).fetchall()
        conn.close()
        if not rows:
            return AgentResponse.ok(
                text="⏰ Напоминаний пока нет.",
                agent_name=self.name,
            )
        lines = ["⏰ Напоминания:"]
        for rid, what, scheduled in rows:
            adapted = self.adapted_time(rid)
            suffix = f" (факт: {adapted})" if adapted else ""
            lines.append(f"  #{rid} — {what} в {scheduled}{suffix}")
        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)


__all__ = ["AgentAdaptiveReminders"]
