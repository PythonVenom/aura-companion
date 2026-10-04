"""T-mesh-1 — DTN-sync для meds (offline).

Наука: RFC 4838 (Delay-Tolerant Networking).
Store-and-forward: если нет сети — кладём в SQLite-очередь,
синхронизируемся при появлении связи.
"""
from __future__ import annotations
import json
import sqlite3
import time
from pathlib import Path

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


DB = Path.home() / ".local/share/aura/meds.db"
QUEUE_DB = Path.home() / ".local/share/aura/dtn_queue.db"


class AgentMedsOffline(MicroAgent):
    name = "meds_offline"

    TRIGGERS = ("офлайн напоминания", "dtn", "оффлайн очередь",
                "напомни вне дома", "когда вернусь")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()
        self._ensure_queue()
        if "статус" in t or "сколько" in t:
            return self._status()
        if "синхрониз" in t or "отправь" in t:
            return self._sync()
        if "очист" in t or "сброс" in t:
            return self._clear()
        return AgentResponse.ok(
            text=f"DTN: {self._count()} в очереди. "
                 "'синхронизируй' / 'статус' / 'очисти'.",
            agent_name=self.name,
        )

    def _ensure_queue(self) -> None:
        QUEUE_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(QUEUE_DB)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dtn_queue (
                id INTEGER PRIMARY KEY,
                kind TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at REAL NOT NULL,
                delivered_at REAL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_delivered ON dtn_queue(delivered_at)")
        conn.commit()
        conn.close()

    def _count(self) -> int:
        conn = sqlite3.connect(QUEUE_DB)
        n = conn.execute(
            "SELECT COUNT(*) FROM dtn_queue WHERE delivered_at IS NULL"
        ).fetchone()[0]
        conn.close()
        return n

    def _status(self) -> AgentResponse:
        conn = sqlite3.connect(QUEUE_DB)
        rows = conn.execute("""
            SELECT kind, payload, created_at FROM dtn_queue
            WHERE delivered_at IS NULL
            ORDER BY created_at DESC LIMIT 5
        """).fetchall()
        total = self._count()
        conn.close()
        if not rows:
            return AgentResponse.ok(
                text="📡 DTN: очередь пуста.", agent_name=self.name,
            )
        lines = [f"📡 DTN: {total} в очереди"]
        for kind, payload, ts in rows:
            age_min = int((time.time() - ts) / 60)
            try:
                p = json.loads(payload)
                preview = p.get("text", payload)[:40]
            except Exception:
                preview = payload[:40]
            lines.append(f"  • [{kind}] {preview} ({age_min}м)")
        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)

    def _sync(self) -> AgentResponse:
        """Симуляция sync: помечаем delivered, отдаём список."""
        conn = sqlite3.connect(QUEUE_DB)
        rows = conn.execute("""
            SELECT id, kind, payload FROM dtn_queue
            WHERE delivered_at IS NULL ORDER BY created_at
        """).fetchall()
        if not rows:
            conn.close()
            return AgentResponse.ok(
                text="📡 DTN: нечего синхронизировать.", agent_name=self.name,
            )
        now = time.time()
        ids = [r[0] for r in rows]
        conn.executemany(
            "UPDATE dtn_queue SET delivered_at=? WHERE id=?",
            [(now, i) for i in ids],
        )
        conn.commit()
        conn.close()
        return AgentResponse.ok(
            text=f"📡 DTN: доставлено {len(rows)} напоминаний.",
            agent_name=self.name,
        )

    def _clear(self) -> AgentResponse:
        conn = sqlite3.connect(QUEUE_DB)
        n = conn.execute(
            "DELETE FROM dtn_queue WHERE delivered_at IS NOT NULL"
        ).rowcount
        conn.commit()
        conn.close()
        return AgentResponse.ok(
            text=f"📡 DTN: очищено {n} доставленных.", agent_name=self.name,
        )

    def enqueue(self, kind: str, payload: dict) -> None:
        """Публичный API: положить в очередь (вызывает meds.py)."""
        self._ensure_queue()
        conn = sqlite3.connect(QUEUE_DB)
        conn.execute(
            "INSERT INTO dtn_queue (kind, payload, created_at) VALUES (?,?,?)",
            (kind, json.dumps(payload, ensure_ascii=False), time.time()),
        )
        conn.commit()
        conn.close()
