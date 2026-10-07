"""GameState — память корабля.

Хранит прогресс капитана между сессиями: XP, ранг, щиты, корпус,
сектор, собранные модули, квесты, день на планете.

Хранение: SQLCipher (AES-256) в ~/.config/aura/state.db.
Ключ: env AURA_DB_KEY или ~/.config/aura/db.key (0600).
"""

from __future__ import annotations

import json
import os
import secrets
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

RANKS: list[tuple[int, str]] = [
    (0, "Кадет"),
    (100, "Лейтенант"),
    (300, "Коммандер"),
    (600, "Капитан"),
    (1000, "Легенда"),
]


def rank_for_xp(xp: int) -> str:
    """Ранг по опыту: Кадет → Лейтенант → Коммандер → Капитан → Легенда."""
    name = "Кадет"
    for threshold, title in RANKS:
        if xp >= threshold:
            name = title
    return name


def level_for_xp(xp: int) -> int:
    """Уровень = индекс текущего ранга + 1."""
    lvl = 1
    for i, (threshold, _) in enumerate(RANKS):
        if xp >= threshold:
            lvl = i + 1
    return lvl


def _default_config_dir() -> Path:
    try:
        from aura.paths import CONFIG_DIR  # type: ignore
        return Path(CONFIG_DIR)
    except Exception:
        return Path.home() / ".config" / "aura"


@dataclass
class GameState:
    """Состояние капитана и корабля."""

    xp: int = 0
    level: int = 1
    rank: str = "Кадет"
    shields: int = 100
    hull: int = 1570
    reactor: int = 100
    sector: str = "STABILIZE"
    modules_active: list[str] = field(default_factory=list)
    modules_total: int = 10
    quests_done: list[str] = field(default_factory=list)
    quests_active: list[str] = field(default_factory=list)
    battles: list[dict] = field(default_factory=list)
    last_seen: str = ""
    landing_date: str = ""

    def __post_init__(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        if not self.last_seen:
            self.last_seen = now
        if not self.landing_date:
            self.landing_date = now
        self.rank = rank_for_xp(self.xp)
        self.level = level_for_xp(self.xp)

    def add_xp(self, amount: int) -> None:
        if amount <= 0:
            return
        self.xp += amount
        self.rank = rank_for_xp(self.xp)
        self.level = level_for_xp(self.xp)

    def days_on_planet(self) -> int:
        try:
            start = datetime.fromisoformat(self.landing_date)
            now = datetime.now(timezone.utc)
            return max(0, (now - start).days) + 1
        except Exception:
            return 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StateStore:
    """SQLCipher-хранилище состояния. Одна JSON-строка в таблице meta."""

    def __init__(self, db_path: Path | None = None, key: str | None = None):
        cfg = _default_config_dir()
        cfg.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path) if db_path else cfg / "state.db"
        self.key = key or self._load_or_make_key(cfg)
        self._conn: sqlite3.Connection | None = None

    def _load_or_make_key(self, cfg: Path) -> str:
        env = os.environ.get("AURA_DB_KEY")
        if env:
            return env
        key_file = cfg / "db.key"
        if key_file.exists():
            return key_file.read_text(encoding="utf-8").strip()
        key = secrets.token_hex(32)
        key_file.write_text(key, encoding="utf-8")
        os.chmod(key_file, 0o600)
        return key

    def _connect(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn
        try:
            from sqlcipher3 import dbapi2 as sqlcipher  # type: ignore
        except ImportError:
            import warnings
            warnings.warn(
                "sqlcipher3 недоступен — используем обычный sqlite (НЕ для прода)",
                RuntimeWarning,
            )
            conn = sqlite3.connect(str(self.db_path))
        else:
            conn = sqlcipher.connect(str(self.db_path))
            conn.execute(f"PRAGMA key = '{self.key}'")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT NOT NULL)"
        )
        self._conn = conn
        return conn

    def load(self) -> GameState:
        conn = self._connect()
        row = conn.execute("SELECT v FROM meta WHERE k = 'state'").fetchone()
        if not row:
            return GameState()
        try:
            data = json.loads(row[0])
        except json.JSONDecodeError:
            return GameState()
        allowed = set(GameState.__dataclass_fields__)
        clean = {k: v for k, v in data.items() if k in allowed}
        return GameState(**clean)

    def save(self, state: GameState) -> None:
        conn = self._connect()
        payload = json.dumps(state.to_dict(), ensure_ascii=False)
        conn.execute(
            "INSERT INTO meta(k, v) VALUES('state', ?) "
            "ON CONFLICT(k) DO UPDATE SET v = excluded.v",
            (payload,),
        )
        conn.execute(
            "INSERT INTO meta(k, v) VALUES('schema_version', ?) "
            "ON CONFLICT(k) DO UPDATE SET v = excluded.v",
            (str(SCHEMA_VERSION),),
        )
        conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
