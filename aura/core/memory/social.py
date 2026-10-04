"""Social Memory — граф семьи (ADR-122 слой 9, ADR-125).

Наука:
- SocialMemBench (2026). Benchmarking Social Memory in LLM Agents.
- PERSONA (2023). Personalized Dialogue via Entity Graphs.
- A-Mem (2025). Agentic Memory with entity relations.

Хранение: SQLite (~/.cache/aura/social.db). Локально. Без облака.

Схема:
  entities(id, name, type, aliases_json, created_at)
  relations(src_id, dst_id, kind, weight, evidence, last_seen)
  events(id, entity_id, kind, date_iso, payload_json)
"""
from __future__ import annotations
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DB_PATH = Path(os.path.expanduser("~/.cache/aura/social.db"))


SCHEMA = """
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type TEXT DEFAULT 'person',
    aliases_json TEXT DEFAULT '[]',
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    src_id INTEGER NOT NULL,
    dst_id INTEGER,
    kind TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    evidence TEXT DEFAULT '',
    last_seen REAL NOT NULL,
    FOREIGN KEY (src_id) REFERENCES entities(id)
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    date_iso TEXT,
    payload_json TEXT DEFAULT '{}',
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);
CREATE INDEX IF NOT EXISTS idx_rel_src ON relations(src_id);
CREATE INDEX IF NOT EXISTS idx_rel_kind ON relations(kind);
CREATE INDEX IF NOT EXISTS idx_evt_entity ON events(entity_id);
"""


@dataclass
class Entity:
    id: int
    name: str
    type: str
    aliases: list[str]


@dataclass
class Relation:
    src: str
    dst: Optional[str]
    kind: str
    weight: float
    evidence: str


class SocialMemory:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._init()

    def _init(self) -> None:
        try:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.executescript(SCHEMA)
            self._conn.commit()
        except Exception as e:
            print(f"⚠️ Social memory init: {e}")
            self._conn = None

    def check_ready(self) -> bool:
        return self._conn is not None

    def upsert_entity(self, name: str, type_: str = "person",
                      aliases: Optional[list[str]] = None) -> Optional[int]:
        if not self._conn:
            return None
        cur = self._conn.execute("SELECT id FROM entities WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            return row["id"]
        cur = self._conn.execute(
            "INSERT INTO entities(name, type, aliases_json, created_at) VALUES (?,?,?,?)",
            (name, type_, json.dumps(aliases or []), time.time()),
        )
        self._conn.commit()
        return cur.lastrowid

    def add_relation(self, src_name: str, kind: str, dst_name: Optional[str] = None,
                     weight: float = 1.0, evidence: str = "") -> bool:
        if not self._conn:
            return False
        src_id = self.upsert_entity(src_name)
        dst_id = self.upsert_entity(dst_name) if dst_name else None
        if src_id is None:
            return False
        self._conn.execute(
            "INSERT INTO relations(src_id, dst_id, kind, weight, evidence, last_seen) "
            "VALUES (?,?,?,?,?,?)",
            (src_id, dst_id, kind, weight, evidence, time.time()),
        )
        self._conn.commit()
        return True

    def add_event(self, entity_name: str, kind: str, date_iso: str = "",
                  payload: Optional[dict] = None) -> bool:
        if not self._conn:
            return False
        eid = self.upsert_entity(entity_name)
        if eid is None:
            return False
        self._conn.execute(
            "INSERT INTO events(entity_id, kind, date_iso, payload_json) VALUES (?,?,?,?)",
            (eid, kind, date_iso, json.dumps(payload or {}, ensure_ascii=False)),
        )
        self._conn.commit()
        return True

    def relations_of(self, name: str, kind: Optional[str] = None) -> list[Relation]:
        if not self._conn:
            return []
        sql = ("SELECT e.name AS src, e2.name AS dst, r.kind, r.weight, r.evidence "
               "FROM relations r JOIN entities e ON r.src_id=e.id "
               "LEFT JOIN entities e2 ON r.dst_id=e2.id "
               "WHERE e.name = ?")
        params: list = [name]
        if kind:
            sql += " AND r.kind = ?"
            params.append(kind)
        sql += " ORDER BY r.last_seen DESC LIMIT 50"
        cur = self._conn.execute(sql, params)
        return [Relation(src=r["src"], dst=r["dst"], kind=r["kind"],
                         weight=r["weight"], evidence=r["evidence"]) for r in cur.fetchall()]

    def events_of(self, name: str, kind: Optional[str] = None) -> list[dict]:
        if not self._conn:
            return []
        sql = ("SELECT ev.kind, ev.date_iso, ev.payload_json "
               "FROM events ev JOIN entities e ON ev.entity_id=e.id WHERE e.name = ?")
        params: list = [name]
        if kind:
            sql += " AND ev.kind = ?"
            params.append(kind)
        sql += " ORDER BY ev.date_iso DESC LIMIT 20"
        cur = self._conn.execute(sql, params)
        return [{"kind": r["kind"], "date": r["date_iso"],
                 "payload": json.loads(r["payload_json"] or "{}")} for r in cur.fetchall()]

    def entities(self) -> list[Entity]:
        if not self._conn:
            return []
        cur = self._conn.execute("SELECT id, name, type, aliases_json FROM entities")
        return [Entity(id=r["id"], name=r["name"], type=r["type"],
                       aliases=json.loads(r["aliases_json"] or "[]"))
                for r in cur.fetchall()]

    def stats(self) -> dict:
        if not self._conn:
            return {"ready": False}
        cur = self._conn.execute("SELECT COUNT(*) AS c FROM entities")
        e = cur.fetchone()["c"]
        cur = self._conn.execute("SELECT COUNT(*) AS c FROM relations")
        r = cur.fetchone()["c"]
        cur = self._conn.execute("SELECT COUNT(*) AS c FROM events")
        ev = cur.fetchone()["c"]
        return {"ready": True, "entities": e, "relations": r, "events": ev}


_SINGLETON: SocialMemory | None = None


def get_social() -> SocialMemory:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = SocialMemory()
    return _SINGLETON
