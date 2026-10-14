"""Medication reminder agent. T022 — MLP бати.

По науке (Czaja et al. 2018): напоминания о лекарствах
снижают пропуски на 40-60%.
"""
from __future__ import annotations

import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent

DB = Path.home() / ".config" / "aura" / "meds.db"


class AgentMeds(BaseAgent):  # AURA_MED_EXTEND_V1
    name = "meds"
    MODULE_ALWAYS = True
    DB = DB  # class attribute (для тестов)

    TRIGGERS = (
        "лекарств", "таблетк", "пилюл", "напомни про", "принять",
        "пора пить", "лекарство", "препарат",
        # AURA_MED_VISITS_V1 + interactions
        "к врачу", "визит", "запис", "стоматолог", "терапевт",
        "окулист", "кардиолог", "невролог", "хирург", "эндокринолог",
        "взаимодейств", "совмест", "вместе приним",
    )

    # AURA_MED_SCHEDULER_V2: scheduler по умолчанию ВЫКЛ.
    #
    # Причина: фоновый _loop + chromadb (Rust FFI) = segfault.
    # SQLite в daemon-потоке конфликтует с Rust-расширениями (GIL).
    #
    # Включается ТОЛЬКО если AURA_MED_SCHEDULER=1 (прод).
    # В тестах и bootstrap — выключен.
    def __init__(self, start_scheduler: bool | None = None):
        super().__init__()
        self._init_db()
        self._scheduler = None

        # Дефолт из env (prod: 1, тесты: 0)
        if start_scheduler is None:
            import os
            start_scheduler = os.environ.get("AURA_MED_SCHEDULER", "0") == "1"

        if start_scheduler:
            self._scheduler = threading.Thread(target=self._loop, daemon=True)
            self._scheduler.start()

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower().strip()
        return any(p in t for p in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        # BUG-FIX: проверка can_handle (как в fall/sos)
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        t = request.text.lower()

        # ВАЖНО: порядок важен! Сначала специфичные ветки.

        # 1. Взаимодействия
        if "взаимодейств" in t or "совмест" in t:
            return self._check_interactions()

        # 2. Визиты (показ)
        VISIT_VIEW = ("покажи визит", "какие визит", "список визит",
                      "мои визит", "записи к врач")
        if any(k in t for k in VISIT_VIEW):
            return self._list_visits()

        # 3. Визиты (добавление)
        DOCTORS = ("терапевт", "стоматолог", "окулист", "кардиолог",
                   "невролог", "хирург", "эндокринолог", "врач")
        if ("к врачу" in t or "визит" in t or "запис" in t
                or any(d in t for d in DOCTORS)):
            # Не показ → добавление
            if "добавь" not in t and "запиши" not in t and "покажи" not in t:
                return self._add_visit(request.text)
            if "покажи" not in t and "какие" not in t and "список" not in t:
                return self._add_visit(request.text)

        # 4. Лекарства — добавление
        if "добавь" in t or "запиши" in t or "напомни" in t:
            return self._add(request.text)

        # 5. Лекарства — список
        if "список" in t or "какие" in t or "покажи" in t:
            return self._list()

        # 6. Принял
        if "принял" in t or "выпил" in t:
            return self._mark_taken()

        # 7. Статус
        return self._status()

    def _init_db(self):
        self.DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.DB)
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
        """Парсинг: «добавь лекарство X в HH:MM»."""
        import re
        # 1. Время
        m = re.search(r"(\d{1,2}:\d{2})", text)
        time_str = m.group(1) if m else "08:00"
        # 2. Имя: убираем «аура», «добавь», «лекарство», время
        name = text.lower()
        for w in ("аура", "добавь", "запиши", "напомни", "лекарство",
                  "таблетки", "таблетку", "препарат"):
            name = name.replace(w, "")
        name = re.sub(r"\d{1,2}:\d{2}", "", name)
        name = re.sub(r"\s+", " ", name).strip(" ,:.-")[:50]
        if not name:
            return AgentResponse.ok(
                text="💊 Что за лекарство? Скажи: «добавь <название> в 08:00»",
                agent_name=self.name,
            )
        conn = sqlite3.connect(self.DB)
        # Dedup: не плодить дубли (boot_report гоняет тесты)
        existing = conn.execute(
            "SELECT id FROM meds WHERE name=? AND time_str=?",
            (name, time_str),
        ).fetchone()
        if existing:
            conn.close()
            return AgentResponse.ok(
                text=f"💊 Уже записано: {name} в {time_str}",
                agent_name=self.name,
            )
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
        conn = sqlite3.connect(self.DB)
        rows = conn.execute("SELECT name, time_str, taken FROM meds").fetchall()
        conn.close()
        if not rows:
            return AgentResponse.ok(text="Список лекарств пуст.", agent_name=self.name)
        lines = [f"{'✅' if r[2] else '⏳'} {r[0]} в {r[1]}" for r in rows]
        return AgentResponse.ok(text="💊 " + "; ".join(lines), agent_name=self.name)

    def _mark_taken(self) -> AgentResponse:
        conn = sqlite3.connect(self.DB)
        conn.execute("UPDATE meds SET taken=1, last_taken=? WHERE taken=0", (int(time.time()),))
        conn.commit()
        conn.close()
        return AgentResponse.ok(text="💊 Отмечено как принято", agent_name=self.name)

    def _status(self) -> AgentResponse:
        conn = sqlite3.connect(self.DB)
        datetime.now().strftime("%H:%M")
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
        conn = sqlite3.connect(self.DB)
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
        conn = sqlite3.connect(self.DB)
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
        conn = sqlite3.connect(self.DB)
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
                conn = sqlite3.connect(self.DB)
                rows = conn.execute(
                    "SELECT id, name FROM meds WHERE time_str=? AND taken=0 AND last_taken<?",
                    (now, int(time.time()) - 3600),
                ).fetchall()
                conn.close()
                for _mid, name in rows:
                    print(f"⏰ MEDS: пора принять {name}", flush=True)
                    # TODO: say() голосом
            except Exception as e:
                # F-006: молчаливый swallow → батя не получит напоминание
                import logging
                logging.getLogger("aura.meds").error(
                    "Meds monitor loop failed: %s", e, exc_info=True)
            time.sleep(30)
