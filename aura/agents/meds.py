"""Medication reminder agent. T022 — MLP бати.

По науке (Czaja et al. 2018): напоминания о лекарствах
снижают пропуски на 40-60%.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


DB = Path.home() / ".config" / "aura" / "meds.db"


class AgentMeds(BaseAgent):  # AURA_MED_EXTEND_V1
    name = "meds"
    MODULE_ALWAYS = True

    TRIGGERS = (
        "лекарств", "таблетк", "пилюл", "напомни про", "принять",
        "пора пить", "лекарство", "препарат",
    )

    def __init__(self):
        super().__init__()
        self._init_db()
        self._scheduler = threading.Thread(target=self._loop, daemon=True)
        self._scheduler.start()

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower().strip()
        return any(p in t for p in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()

        if "добавь" in t or "запиши" in t or "напомни" in t:
            return self._add(request.text)

        if "список" in t or "какие" in t or "покажи" in t:
            return self._list()

        if "принял" in t or "выпил" in t:
            return self._mark_taken()
        # AURA_MED_VISITS_V1 — визиты и взаимодействие
        if "к врачу" in t or "визит" in t or "запис" in t:
            if "покажи" in t or "какие" in t or "список" in t:
                return self._list_visits()
            return self._add_visit(request.text)
        if "взаимодейств" in t or "совмест" in t or "вместе" in t:
            return self._check_interactions()

        return self._status()

    def _init_db(self):
        DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS meds (
                id INTEGER PRIMARY KEY,
                name TEXT,
                dose TEXT,
                time_str TEXT,
                taken INTEGER DEFAULT 0,
                last_taken INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS allergies (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                reaction TEXT,
                severity TEXT
            );
            CREATE TABLE IF NOT EXISTS diagnoses (
                id INTEGER PRIMARY KEY,
                name TEXT,
                icd TEXT,
                since TEXT
            );
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY,
                doctor TEXT,
                when_text TEXT,
                time_str TEXT,
                notes TEXT
            );
            CREATE TABLE IF NOT EXISTS emergency_contacts (
                id INTEGER PRIMARY KEY,
                name TEXT,
                phone TEXT,
                relation TEXT,
                priority INTEGER DEFAULT 10
            )
        """)
        conn.commit()
        conn.close()

    def _add(self, text: str) -> AgentResponse:
        # Упрощённый парсинг: "аура, добавь лекарство X в HH:MM"
        import re
        m = re.search(r"(\d{1,2}:\d{2})", text)
        time_str = m.group(1) if m else "08:00"
        name = text.replace("аура", "").replace("добавь", "").strip()[:50]
        conn = sqlite3.connect(DB)
        conn.execute(
            "INSERT INTO meds (name, time_str) VALUES (?, ?)",
            (name, time_str),
        )
        conn.commit()
        conn.close()
        return AgentResponse.ok(
            text=f"💊 Запомнила: {name} в {time_str}",
            agent_name=self.name,
        )

    def _list(self) -> AgentResponse:
        conn = sqlite3.connect(DB)
        rows = conn.execute("SELECT name, time_str, taken FROM meds").fetchall()
        conn.close()
        if not rows:
            return AgentResponse.ok(text="Список лекарств пуст.", agent_name=self.name)
        lines = [f"{'✅' if r[2] else '⏳'} {r[0]} в {r[1]}" for r in rows]
        return AgentResponse.ok(text="💊 " + "; ".join(lines), agent_name=self.name)

    def _mark_taken(self) -> AgentResponse:
        conn = sqlite3.connect(DB)
        conn.execute("UPDATE meds SET taken=1, last_taken=? WHERE taken=0", (int(time.time()),))
        conn.commit()
        conn.close()
        return AgentResponse.ok(text="💊 Отмечено как принято", agent_name=self.name)

    def _status(self) -> AgentResponse:
        conn = sqlite3.connect(DB)
        now = datetime.now().strftime("%H:%M")
        rows = conn.execute(
            "SELECT name, time_str FROM meds WHERE taken=0 ORDER BY time_str"
        ).fetchall()
        conn.close()
        if not rows:
            return AgentResponse.ok(text="Все лекарства приняты.", agent_name=self.name)
        return AgentResponse.ok(
            text=f"⏳ Осталось: {', '.join(f'{r[0]} ({r[1]})' for r in rows)}",
            agent_name=self.name,
        )

    # AURA_MED_VISITS_V1 — T024 визиты к врачу
    def _add_visit(self, text: str) -> AgentResponse:
        """Добавить визит к врачу. Формат: 'к врачу в 15:00 завтра'."""
        import re
        m = re.search(r"(\d{1,2}:\d{2})", text)
        time_str = m.group(1) if m else "10:00"
        when = "завтра" if "завтра" in text.lower() else "сегодня"
        doctor = self._extract_doctor(text)
        conn = sqlite3.connect(DB)
        conn.execute(
            "INSERT INTO visits (doctor, when_text, time_str) VALUES (?, ?, ?)",
            (doctor, when, time_str),
        )
        conn.commit()
        conn.close()
        return AgentResponse.ok(
            text=f"🏥 Записала: {doctor} {when} в {time_str}",
            agent_name=self.name,
        )

    def _extract_doctor(self, text: str) -> str:
        """Простой парсер: 'к терапевту', 'к стоматологу' и т.п."""
        for kw in ("терапевт", "стоматолог", "окулист", "кардиолог",
                   "невролог", "хирург", "эндокринолог", "врач"):
            if kw in text.lower():
                return kw
        return "врач"

    def _list_visits(self) -> AgentResponse:
        conn = sqlite3.connect(DB)
        rows = conn.execute(
            "SELECT doctor, when_text, time_str FROM visits ORDER BY id DESC LIMIT 5"
        ).fetchall()
        conn.close()
        if not rows:
            return AgentResponse.ok(text="📅 Визитов нет.", agent_name=self.name)
        lines = [f"  • {r[0]} {r[1]} в {r[2]}" for r in rows]
        return AgentResponse.ok(
            text="📅 Визиты:\n" + "\n".join(lines),
            agent_name=self.name,
        )

    # T025 взаимодействие лекарств
    INTERACTIONS = {
        frozenset(["аспирин", "варфарин"]): "⚠️ Кровотечение",
        frozenset(["аспирин", "ибупрофен"]): "⚠️ Язва желудка",
        frozenset(["омепразол", "клопидогрел"]): "⚠️ Снижение эффекта",
        frozenset(["метформин", "алкоголь"]): "⚠️ Лактоацидоз",
        frozenset(["парацетамол", "алкоголь"]): "⚠️ Токсичность печени",
    }

    def _check_interactions(self) -> AgentResponse:
        conn = sqlite3.connect(DB)
        rows = conn.execute("SELECT name FROM meds WHERE taken=0").fetchall()
        conn.close()
        names = [r[0].lower() for r in rows]
        warnings = []
        for pair, msg in self.INTERACTIONS.items():
            if all(any(x in n for n in names) for x in pair):
                warnings.append(f"  • {' + '.join(pair)}: {msg}")
        if not warnings:
            return AgentResponse.ok(
                text="💊 Взаимодействий не найдено.",
                agent_name=self.name,
            )
        return AgentResponse.ok(
            text="💊 ВОЗМОЖНЫЕ ВЗАИМОДЕЙСТВИЯ:\n" + "\n".join(warnings),
            agent_name=self.name,
        )

    def _loop(self):
        """Фоновый демон: раз в 30 сек проверяет время приёма."""
        while True:
            try:
                now = datetime.now().strftime("%H:%M")
                conn = sqlite3.connect(DB)
                rows = conn.execute(
                    "SELECT id, name FROM meds WHERE time_str=? AND taken=0 AND last_taken<?",
                    (now, int(time.time()) - 3600),
                ).fetchall()
                conn.close()
                for mid, name in rows:
                    print(f"⏰ MEDS: пора принять {name}", flush=True)
                    # TODO: say() голосом
            except Exception as e:
                # F-006: молчаливый swallow → батя не получит напоминание
                import logging
                logging.getLogger("aura.meds").error(
                    "Meds monitor loop failed: %s", e, exc_info=True)
            time.sleep(30)
