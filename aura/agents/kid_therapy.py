"""T056 — игровая терапия для ребёнка.

Наука:
- Landreth 2012 «Play Therapy: The Art of the Relationship»
- Axline 1947 — 8 принципов недирективной игротерапии
- Возрастные категории: 2-4 / 5-7 / 8-10
"""
from __future__ import annotations
import random
import sqlite3
import time
from pathlib import Path

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


THERAPY_DB = Path.home() / ".local/share/aura/kid.db"


# Axline 1947 + Landreth 2012 — базовые упражнения
EXERCISES = {
    "2-4": [
        ("Сенсорика", "Пересыпание крупы: 2 миски, ложка. Проговорить «полная/пустая»."),
        ("Крупная моторика", "Перешагивание через подушку. «высоко-низко»."),
        ("Речь", "Называем части тела в зеркале: «где носик?»"),
        ("Эмоции", "Карточки: «зайка грустный / весёлый». Показать лицом."),
    ],
    "5-7": [
        ("Ролевая игра", "«В магазин»: продавец-покупатель. Считаем 1-5."),
        ("Мелкая моторика", "Пластилин: лепим круг, квадрат, называем."),
        ("Эмоции", "Кубик эмоций: 6 граней — 6 настроений. Кидаем, изображаем."),
        ("Счёт", "Сортировка пуговиц по цвету, потом по размеру."),
    ],
    "8-10": [
        ("Логика", "Настольная игра на 2 хода вперёд (шашки, крестики)."),
        ("Эмоции", "Дневник настроения: 3 слова о дне каждый вечер."),
        ("Речь", "Рассказ по 4 картинкам: начало-середина-конец."),
        ("Социальное", "Ролевая: «как попросить игрушку у друга»."),
    ],
}


class AgentKidTherapy(MicroAgent):
    name = "kid_therapy"

    TRIGGERS = ("игровая терапия", "упражнение для ребёнка", "поиграй с ребёнком",
                "развивающее", "терапевтическая игра", "чем занять ребёнка")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        self._ensure()
        t = request.text.lower()

        if "историю" in t or "что делали" in t or "лог" in t:
            return self._history()
        if "возраст" in t:
            return self._set_age(request.text)

        return self._suggest(request.text)

    def _ensure(self) -> None:
        THERAPY_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(THERAPY_DB)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS therapy (
                id INTEGER PRIMARY KEY,
                age_group TEXT NOT NULL,
                exercise TEXT NOT NULL,
                done_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kid_state (
                key TEXT PRIMARY KEY,
                val TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def _get_age(self) -> str:
        conn = sqlite3.connect(THERAPY_DB)
        row = conn.execute(
            "SELECT val FROM kid_state WHERE key='age_group'"
        ).fetchone()
        conn.close()
        return row[0] if row else "5-7"

    def _set_age(self, text: str) -> AgentResponse:
        import re
        m = re.search(r"(\d+)", text)
        if not m:
            return AgentResponse.ok(text="Формат: 'возраст ребёнка 6'", agent_name=self.name)
        age = int(m.group(1))
        if age < 5:
            group = "2-4"
        elif age < 8:
            group = "5-7"
        else:
            group = "8-10"
        conn = sqlite3.connect(THERAPY_DB)
        conn.execute(
            "INSERT OR REPLACE INTO kid_state (key, val) VALUES ('age_group', ?)",
            (group,),
        )
        conn.commit()
        conn.close()
        return AgentResponse.ok(
            text=f"✅ Возраст: {age}, группа {group}.",
            agent_name=self.name,
        )

    def _suggest(self, text: str) -> AgentResponse:
        age = self._get_age()
        pool = EXERCISES.get(age, EXERCISES["5-7"])

        # Не повторять последнее (Axline: дать выбор)
        conn = sqlite3.connect(THERAPY_DB)
        last = conn.execute(
            "SELECT exercise FROM therapy ORDER BY id DESC LIMIT 3"
        ).fetchall()
        conn.close()
        last_titles = {r[0] for r in last}

        candidates = [e for e in pool if e[0] not in last_titles] or pool
        title, instruction = random.choice(candidates)

        # Записать
        conn = sqlite3.connect(THERAPY_DB)
        conn.execute(
            "INSERT INTO therapy (age_group, exercise, done_at) VALUES (?, ?, ?)",
            (age, title, time.time()),
        )
        conn.commit()
        conn.close()

        return AgentResponse.ok(
            text=f"🎲 Упражнение ({age}, {title}):\n{instruction}",
            agent_name=self.name,
        )

    def _history(self) -> AgentResponse:
        conn = sqlite3.connect(THERAPY_DB)
        rows = conn.execute(
            "SELECT exercise, age_group, done_at FROM therapy "
            "ORDER BY id DESC LIMIT 10"
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM therapy").fetchone()[0]
        conn.close()
        if not rows:
            return AgentResponse.ok(
                text="🧩 История пуста. Скажи 'упражнение для ребёнка'.",
                agent_name=self.name,
            )
        lines = [f"🧩 Проведено: {total}"]
        for ex, age, ts in rows:
            days = int((time.time() - ts) / 86400)
            lines.append(f"  • [{age}] {ex} ({days}д)")
        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)
