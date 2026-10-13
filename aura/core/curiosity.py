"""#11 Curiosity Engine — внутренняя мотивация задавать вопросы.

Наука:
- Berlyne 1960 — Curiosity and Exploration (конфликт/новизна)
- Loewenstein 1994 — The Psychology of Curiosity (information gap theory)
- Schmidhuber 1991 — Formal Theory of Fun (compression progress)
- Oudeyer & Kaplan 2007 — Intrinsic Motivation Systems

Идея:
  Aura отслеживает "information gaps" — пробелы в знаниях.
  Каждый gap имеет:
    - topic (тема)
    - confidence (насколько уверена, что знает — 0..1)
    - importance (важность для пользователя — 0..1)
    - last_asked (timestamp, защита от спама)

  pick_question() выбирает самый "созревший" gap:
    priority = importance * (1 - confidence) * recency_factor

  record_answer() повышает confidence после ответа пользователя/LLM.

Пути:
  ~/.local/share/aura/curiosity.db

Отличие от #14 Initiative:
  Initiative — реагирует на события (Meds, Health, Proactive).
  Curiosity — задаёт вопросы в "тишине", чтобы учиться.

Отличие от #13 Learnings:
  Learnings — пассивная память.
  Curiosity — активный процесс генерации вопросов.
"""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

DB = Path.home() / ".local/share/aura/curiosity.db"

# Через сколько секунд можно снова задать вопрос по тому же gap
COOLDOWN_SEC = 3600  # 1 час

# Минимальный приоритет для вопроса
MIN_PRIORITY = 0.2


@dataclass
class Gap:
    topic: str
    confidence: float = 0.0      # 0..1
    importance: float = 0.5      # 0..1
    last_asked: float = 0.0
    ask_count: int = 0

    def priority(self, now: float | None = None) -> float:
        """Приоритет = важность × незнание × свежесть."""
        now = now or time.time()
        ignorance = 1.0 - self.confidence
        # Свежесть: если давно спрашивали — приоритет растёт
        age_hours = (now - self.last_asked) / 3600.0 if self.last_asked else 999.0
        recency = min(1.0, age_hours / 24.0)  # 1.0 после суток
        return self.importance * ignorance * recency


def _ensure_db() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gaps (
            topic TEXT PRIMARY KEY,
            confidence REAL NOT NULL DEFAULT 0.0,
            importance REAL NOT NULL DEFAULT 0.5,
            last_asked REAL NOT NULL DEFAULT 0.0,
            ask_count INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


class CuriosityEngine:
    """Движок любопытства Aura."""

    def __init__(self) -> None:
        _ensure_db()

    # ─── Регистрация пробела ───
    def register_gap(self, topic: str, importance: float = 0.5) -> Gap:
        """Добавить или обновить пробел в знаниях."""
        topic = topic.strip().lower()
        if not topic:
            raise ValueError("topic не может быть пустым")
        importance = max(0.0, min(1.0, importance))

        conn = sqlite3.connect(DB)
        row = conn.execute(
            "SELECT confidence, importance, last_asked, ask_count FROM gaps WHERE topic=?",
            (topic,),
        ).fetchone()
        if row:
            # Обновляем важность (берём максимум)
            new_imp = max(row[1], importance)
            conn.execute(
                "UPDATE gaps SET importance=? WHERE topic=?", (new_imp, topic)
            )
            conn.commit()
            conn.close()
            return Gap(topic, row[0], new_imp, row[2], row[3])
        conn.execute(
            "INSERT INTO gaps (topic, confidence, importance) VALUES (?, 0.0, ?)",
            (topic, importance),
        )
        conn.commit()
        conn.close()
        return Gap(topic, 0.0, importance)

    # ─── Выбор вопроса ───
    def pick_question(self, threshold: float = MIN_PRIORITY) -> Gap | None:
        """Выбрать самый приоритетный gap для вопроса."""
        gaps = self.list_gaps()
        now = time.time()
        candidates = [
            g for g in gaps
            if g.priority(now) >= threshold
            and (now - g.last_asked) >= COOLDOWN_SEC
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda g: g.priority(now))

    # ─── Запись ответа ───
    def record_answer(self, topic: str, confidence_delta: float = 0.3) -> bool:
        """Пользователь/LLM ответил → повышаем confidence."""
        topic = topic.strip().lower()
        conn = sqlite3.connect(DB)
        row = conn.execute(
            "SELECT confidence FROM gaps WHERE topic=?", (topic,)
        ).fetchone()
        if not row:
            conn.close()
            return False
        new_conf = min(1.0, row[0] + confidence_delta)
        conn.execute(
            "UPDATE gaps SET confidence=?, last_asked=?, ask_count=ask_count+1 WHERE topic=?",
            (new_conf, time.time(), topic),
        )
        conn.commit()
        conn.close()
        return True

    # ─── Список ───
    def list_gaps(self) -> list[Gap]:
        conn = sqlite3.connect(DB)
        rows = conn.execute(
            "SELECT topic, confidence, importance, last_asked, ask_count FROM gaps"
        ).fetchall()
        conn.close()
        return [Gap(*r) for r in rows]

    # ─── Статистика ───
    def stats(self) -> dict:
        gaps = self.list_gaps()
        if not gaps:
            return {
                "total": 0, "known": 0, "unknown": 0,
                "avg_confidence": 0.0, "avg_priority": 0.0,
            }
        known = sum(1 for g in gaps if g.confidence >= 0.8)
        unknown = sum(1 for g in gaps if g.confidence < 0.3)
        return {
            "total": len(gaps),
            "known": known,
            "unknown": unknown,
            "avg_confidence": round(sum(g.confidence for g in gaps) / len(gaps), 3),
            "avg_priority": round(sum(g.priority() for g in gaps) / len(gaps), 3),
        }

    # ─── Очистка ───
    def forget(self, topic: str) -> bool:
        topic = topic.strip().lower()
        conn = sqlite3.connect(DB)
        cur = conn.execute("DELETE FROM gaps WHERE topic=?", (topic,))
        conn.commit()
        deleted = cur.rowcount > 0
        conn.close()
        return deleted


__all__ = ["CuriosityEngine", "Gap", "DB", "COOLDOWN_SEC", "MIN_PRIORITY"]
