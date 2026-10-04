"""T055 — структура дня ребёнка.

Наука:
- TEACCH (Mesibov 2005) — структурированное обучение
- Visual Schedules — предсказуемость снижает тревогу
- Routine-Based Intervention — ритуалы и повторяемость
"""
from __future__ import annotations
import json
import sqlite3
import time
from pathlib import Path

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


KID_DB = Path.home() / ".local/share/aura/kid.db"


class AgentKidStructure(MicroAgent):
    name = "kid_structure"

    TRIGGERS = ("расписание ребёнка", "режим дня", "что делать с ребёнком",
                "школа", "кружок", "ритуал", "утренние дела",
                "структура дня", "распорядок")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        self._ensure()
        t = request.text.lower()

        if "покажи" in t or "какое" in t or "расписание на сегодня" in t:
            return self._today()
        if "добавь" in t or "запиши" in t:
            return self._add(request.text)
        if "выполнил" in t or "сделал" in t or "готово" in t:
            return self._done(request.text)
        if "ритуал" in t:
            return self._rituals()
        return AgentResponse.ok(
            text="Расписание ребёнка. "
                 "'покажи на сегодня' / 'добавь <дело> в <время>' / "
                 "'выполнил <дело>' / 'ритуалы'",
            agent_name=self.name,
        )

    def _ensure(self) -> None:
        KID_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(KID_DB)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                time_hhmm TEXT NOT NULL,
                title TEXT NOT NULL,
                kind TEXT,
                done_date TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rituals (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                steps TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def _today(self) -> AgentResponse:
        conn = sqlite3.connect(KID_DB)
        rows = conn.execute(
            "SELECT time_hhmm, title, kind, done_date FROM events "
            "ORDER BY time_hhmm"
        ).fetchall()
        conn.close()
        if not rows:
            return AgentResponse.ok(
                text="📅 Расписание пусто. 'добавь зарядку в 07:30'",
                agent_name=self.name,
            )
        today = time.strftime("%Y-%m-%d")
        lines = [f"📅 Расписание на {today}:"]
        for hhmm, title, kind, done_date in rows:
            mark = "✅" if done_date == today else "☐"
            kind_s = f" [{kind}]" if kind else ""
            lines.append(f"  {mark} {hhmm} — {title}{kind_s}")
        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)

    def _add(self, text: str) -> AgentResponse:
        import re
        m = re.search(r"добав[ьи]\s+(.+?)\s+в\s+(\d{1,2}[:.]\d{2})", text.lower())
        if not m:
            return AgentResponse.ok(
                text="Формат: 'добавь зарядку в 07:30'",
                agent_name=self.name,
            )
        title, raw_time = m.group(1).strip(), m.group(2).replace(".", ":")
        hh, mm = raw_time.split(":")
        hhmm = f"{int(hh):02d}:{mm}"

        kind = None
        for k in ("школа", "кружок", "еда", "сон", "игра", "прогулка", "зарядка"):
            if k in title:
                kind = k
                break

        conn = sqlite3.connect(KID_DB)
        conn.execute(
            "INSERT INTO events (time_hhmm, title, kind) VALUES (?, ?, ?)",
            (hhmm, title, kind),
        )
        conn.commit()
        conn.close()
        return AgentResponse.ok(
            text=f"✅ Добавлено: {hhmm} — {title}",
            agent_name=self.name,
        )

    def _done(self, text: str) -> AgentResponse:
        import re
        m = re.search(r"(?:выполнил|сделал|готово)\s+(.+)", text.lower())
        if not m:
            return AgentResponse.ok(text="Формат: 'выполнил зарядку'", agent_name=self.name)
        needle = f"%{m.group(1).strip()}%"
        today = time.strftime("%Y-%m-%d")
        conn = sqlite3.connect(KID_DB)
        cur = conn.execute(
            "UPDATE events SET done_date=? WHERE title LIKE ?",
            (today, needle),
        )
        conn.commit()
        changed = cur.rowcount
        conn.close()
        if not changed:
            return AgentResponse.ok(
                text=f"⚠️ Не нашла '{m.group(1)}'",
                agent_name=self.name,
            )
        return AgentResponse.ok(
            text=f"✅ Отмечено: {changed} дел(о).",
            agent_name=self.name,
        )

    def _rituals(self) -> AgentResponse:
        conn = sqlite3.connect(KID_DB)
        rows = conn.execute("SELECT name, steps FROM rituals").fetchall()
        conn.close()
        if not rows:
            defaults = [
                ("утро", "умыться → зарядка → завтрак → собраться"),
                ("вечер", "ужин → купание → сказка → сон"),
                ("перед сном", "умыться → пижама → сказка → свет"),
            ]
            conn = sqlite3.connect(KID_DB)
            for name, steps in defaults:
                conn.execute(
                    "INSERT OR IGNORE INTO rituals (name, steps) VALUES (?, ?)",
                    (name, steps),
                )
            conn.commit()
            conn.close()
            rows = [(n, s) for n, s in defaults]
        lines = ["🔁 Ритуалы:"]
        for name, steps in rows:
            lines.append(f"  • {name}: {steps}")
        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)
