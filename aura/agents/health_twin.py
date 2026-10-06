"""T-twin-1 — Human Digital Twin (temporal graph).

Наука:
- Dimitrov 2021 — Human Digital Twin
- Ji et al. 2021 — Temporal Knowledge Graph (ACM Computing Surveys)
- Fowler 2005 — Event Sourcing
- Kraus 2020 — Medical timelines

Идея: все события здоровья (лекарства, эмоции, напоминания, визиты) —
узлы временного графа. Между ними — связи (caused_by, followed_by, related).
Запросы: временной срез, путь между событиями, поиск паттернов.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse

TWIN_DB = Path.home() / ".local/share/aura/health_twin.db"


class AgentHealthTwin(MicroAgent):
    name = "health_twin"

    TRIGGERS = ("двойник", "twin", "история здоровья", "timeline",
                "что было в", "связь между", "паттерн", "цифровой двойник")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        self._ensure()
        t = request.text.lower()

        if "timeline" in t or "что было в" in t or "за последние" in t:
            return self._timeline(request.text)
        if "связь между" in t or "почему" in t:
            return self._trace(request.text)
        if "паттерн" in t or "повторяется" in t:
            return self._patterns()
        if "статус" in t:
            return self._status()

        return AgentResponse.ok(
            text="🧬 Двойник. "
                 "'timeline за 7 дней' / 'связь между X и Y' / "
                 "'паттерны' / 'статус'",
            agent_name=self.name,
        )

    def _ensure(self) -> None:
        TWIN_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(TWIN_DB)
        # Узлы графа = события
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                ts REAL NOT NULL,
                kind TEXT NOT NULL,
                subject TEXT,
                payload TEXT
            )
        """)
        # Связи графа = рёбра
        conn.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY,
                from_id INTEGER NOT NULL,
                to_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                note TEXT,
                FOREIGN KEY (from_id) REFERENCES events(id),
                FOREIGN KEY (to_id) REFERENCES events(id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_kind ON events(kind)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_to ON edges(to_id)")
        conn.commit()
        conn.close()

    # --- Публичный API ---

    def add_event(self, kind: str, subject: str, payload: dict,
                  ts: float | None = None) -> int:
        """Добавить узел. Вызывают другие агенты (meds, emotion, proactive)."""
        self._ensure()
        conn = sqlite3.connect(TWIN_DB)
        cur = conn.execute(
            "INSERT INTO events (ts, kind, subject, payload) VALUES (?, ?, ?, ?)",
            (ts or time.time(), kind, subject,
             json.dumps(payload, ensure_ascii=False)),
        )
        eid = cur.lastrowid
        conn.commit()
        conn.close()
        return eid

    def add_edge(self, from_id: int, to_id: int, kind: str,
                 note: str = "") -> int:
        """Связать два события."""
        self._ensure()
        conn = sqlite3.connect(TWIN_DB)
        cur = conn.execute(
            "INSERT INTO edges (from_id, to_id, kind, note) VALUES (?, ?, ?, ?)",
            (from_id, to_id, kind, note),
        )
        eid = cur.lastrowid
        conn.commit()
        conn.close()
        return eid

    # --- Запросы ---

    def _timeline(self, text: str) -> AgentResponse:
        import re
        m = re.search(r"за\s+(\d+)\s*(дн|день|дня|недел|час|ч)", text.lower())
        days = 7
        if m:
            n = int(m.group(1))
            unit = m.group(2)
            if unit.startswith("час") or unit.startswith("ч"):
                days = n / 24.0
            elif unit.startswith("недел"):
                days = n * 7
            else:
                days = n
        since = time.time() - days * 86400
        conn = sqlite3.connect(TWIN_DB)
        rows = conn.execute(
            "SELECT id, ts, kind, subject, payload FROM events "
            "WHERE ts >= ? ORDER BY ts",
            (since,),
        ).fetchall()
        conn.close()
        if not rows:
            return AgentResponse.ok(
                text=f"🧬 Событий за {days:.0f}д нет.",
                agent_name=self.name,
            )
        lines = [f"🧬 Timeline за {days:.0f}д ({len(rows)} событий):"]
        for _eid, ts, kind, subject, payload in rows[-20:]:
            when = time.strftime("%m-%d %H:%M", time.localtime(ts))
            preview = ""
            try:
                p = json.loads(payload)
                preview = str(p.get("text") or p.get("name") or "")[:40]
            except Exception:
                preview = (payload or "")[:40]
            lines.append(f"  [{when}] {kind}: {subject} {preview}")
        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)

    def _trace(self, text: str) -> AgentResponse:
        """Найти путь между событиями с ключевыми словами."""
        import re
        m = re.search(r"между\s+(.+?)\s+и\s+(.+)", text.lower())
        if not m:
            return AgentResponse.ok(
                text="Формат: 'связь между <X> и <Y>'",
                agent_name=self.name,
            )
        a, b = m.group(1).strip(), m.group(2).strip()
        conn = sqlite3.connect(TWIN_DB)
        # Простой graph walk в ширину, depth = 3
        def find_ids(needle: str) -> list[int]:
            rows = conn.execute(
                "SELECT id FROM events WHERE subject LIKE ? OR payload LIKE ? LIMIT 20",
                (f"%{needle}%", f"%{needle}%"),
            ).fetchall()
            return [r[0] for r in rows]
        starts, targets = set(find_ids(a)), set(find_ids(b))
        if not starts or not targets:
            conn.close()
            return AgentResponse.ok(
                text=f"🧬 Один из узлов не найден: '{a}' или '{b}'.",
                agent_name=self.name,
            )
        # BFS depth=3
        from collections import deque
        visited, q = set(), deque((s, [s]) for s in starts)
        path = None
        depth_limit = 3
        while q:
            node, path_so_far = q.popleft()
            if node in targets:
                path = path_so_far
                break
            if len(path_so_far) > depth_limit:
                continue
            visited.add(node)
            nbrs = conn.execute(
                "SELECT to_id FROM edges WHERE from_id=? "
                "UNION SELECT from_id FROM edges WHERE to_id=?",
                (node, node),
            ).fetchall()
            for (nid,) in nbrs:
                if nid not in visited:
                    q.append((nid, [*path_so_far, nid]))
        conn.close()
        if not path:
            return AgentResponse.ok(
                text=f"🧬 Прямой связи между '{a}' и '{b}' не нашла (depth≤3).",
                agent_name=self.name,
            )
        return AgentResponse.ok(
            text=f"🧬 Путь ({len(path)-1} шагов): {' → '.join(f'#{i}' for i in path)}",
            agent_name=self.name,
        )

    def _patterns(self) -> AgentResponse:
        """Простые паттерны: повторяющиеся kinds по времени."""
        conn = sqlite3.connect(TWIN_DB)
        rows = conn.execute("""
            SELECT kind, strftime('%H', ts, 'unixepoch', 'localtime') AS hh,
                   COUNT(*) AS n
            FROM events
            GROUP BY kind, hh
            HAVING n >= 3
            ORDER BY n DESC LIMIT 10
        """).fetchall()
        conn.close()
        if not rows:
            return AgentResponse.ok(
                text="🧬 Повторяющихся паттернов пока нет (нужно ≥3 повторов).",
                agent_name=self.name,
            )
        lines = ["🧬 Паттерны:"]
        for kind, hh, n in rows:
            lines.append(f"  • {kind} в {hh}:00 — {n} раз")
        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)

    def _status(self) -> AgentResponse:
        conn = sqlite3.connect(TWIN_DB)
        e = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        ed = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        if e:
            first = conn.execute("SELECT MIN(ts) FROM events").fetchone()[0]
            days = (time.time() - first) / 86400.0
        else:
            days = 0
        conn.close()
        return AgentResponse.ok(
            text=f"🧬 Двойник: {e} событий, {ed} связей, история {days:.1f}д.",
            agent_name=self.name,
        )
