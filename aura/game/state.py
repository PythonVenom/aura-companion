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
from datetime import UTC, datetime
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
    # Прогресс корабля (сборка)
    progress: float = 0.0
    tests_passing: int = 0
    modules_working: int = 0
    modules_broken: int = 0
    # F-101: какие сектора видел капитан (для отката)
    visited_sectors: list[str] = field(default_factory=list)
    max_chapter_reached: int = 0
    modules_active: list[str] = field(default_factory=list)
    modules_total: int = 10
    quests_done: list[str] = field(default_factory=list)
    quests_active: list[str] = field(default_factory=list)
    battles: list[dict] = field(default_factory=list)
    last_seen: str = ""
    landing_date: str = ""

    def __post_init__(self) -> None:
        now = datetime.now(UTC).isoformat()
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
            now = datetime.now(UTC)
            return max(0, (now - start).days) + 1
        except Exception:
            return 1



    def mark_visited(self, sector: str, chapter: int = 0) -> None:
        """Отметить сектор как посещённый. Обновляет max_chapter."""
        if sector and sector not in self.visited_sectors:
            self.visited_sectors.append(sector)
        if chapter > self.max_chapter_reached:
            self.max_chapter_reached = chapter

    def can_return_to(self, sector: str) -> bool:
        """Можно ли вернуться в сектор (его видели)."""
        return sector in self.visited_sectors or sector == self.sector

    def recalc_progress(self) -> float:
        """Пересчёт сборки корабля (0-100%).

        Формула:
          корпус (тесты) 50%  → tests_passing / 2000
          модули (агенты) 30% → modules_working / 100
          щиты (чистота) 20%  → 0 багов = 20, каждый баг -2
        """
        # Корпус — 50%
        hull_pct = min(1.0, self.tests_passing / 2000) * 50.0

        # Модули — 30%
        mod_pct = min(1.0, self.modules_working / 100) * 30.0

        # Щиты — 20%
        shield_pct = max(0.0, 20.0 - self.modules_broken * 2.0)

        self.progress = round(hull_pct + mod_pct + shield_pct, 1)
        return self.progress

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StateStore:
    """SQLCipher-хранилище состояния. Одна JSON-строка в таблице meta."""

    def __init__(self, db_path: Path | None = None, key: str | None = None):
        cfg = _default_config_dir()
        cfg.mkdir(parents=True, exist_ok=True)
        if db_path:
            self.db_path = Path(db_path)
        else:
            # F-068: профиль
            try:
                from aura.profiles import get_profile
                self.db_path = get_profile().state_db
            except Exception:
                self.db_path = cfg / "state.db"
        self.key = key or self._load_or_make_key(cfg)
        self._conn: sqlite3.Connection | None = None

    KEYRING_SERVICE = "aura-game-state"
    KEYRING_USER = "master-key"

    def _load_or_make_key(self, cfg: Path) -> str:
        """Получить ключ SQLCipher.

        Приоритет (миграция 2026-10-13, AUDIT #3):
        1. env AURA_DB_KEY — для контейнеров/CI
        2. keyring — системное шифрованное хранилище (freedesktop Secret Service)
        3. Миграция: если есть ~/.config/aura/db.key — переносим в keyring,
           файл удаляем.

        Наука: Saltzer & Schroeder 1975 (least privilege, fail-safe defaults).
        """
        # 1. env
        env = os.environ.get("AURA_DB_KEY")
        if env:
            return env

        # 2. keyring
        try:
            import keyring
            key = keyring.get_password(self.KEYRING_SERVICE, self.KEYRING_USER)
            if key:
                return key
        except Exception:
            keyring = None  # type: ignore

        # 3. Миграция с plaintext
        key_file = cfg / "db.key"
        if key_file.exists():
            key = key_file.read_text(encoding="utf-8").strip()
            try:
                import keyring
                keyring.set_password(self.KEYRING_SERVICE, self.KEYRING_USER, key)
                key_file.unlink()
                import logging
                logging.getLogger("aura.game.state").info(
                    "Ключ SQLCipher мигрирован в keyring, plaintext удалён"
                )
            except Exception:
                pass  # keyring недоступен — остаёмся на файле
            return key

        # 4. Новый ключ — только в keyring
        key = secrets.token_hex(32)
        try:
            import keyring
            keyring.set_password(self.KEYRING_SERVICE, self.KEYRING_USER, key)
        except Exception:
            # Fallback: файл (last resort)
            key_file.write_text(key, encoding="utf-8")
            os.chmod(key_file, 0o600)
            import logging
            logging.getLogger("aura.game.state").warning(
                "keyring недоступен — ключ в plaintext файле %s", key_file
            )
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
                stacklevel=2,
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
