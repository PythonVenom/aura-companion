"""T-sec-4 — Consent flow (GDPR Art.7 + 152-ФЗ ст.9).

Наука:
- GDPR Art.7 — Conditions for consent (explicit, revocable)
- GDPR Art.17 — Right to erasure
- 152-ФЗ ст.9 — Согласие субъекта
- ISO 29184 — Online privacy notices and consent
- Nissenbaum 2004 — Contextual integrity

Принципы:
1. Explicit — пользователь активно выбирает
2. Granular — согласие на каждый scope отдельно
3. Revocable — можно отозвать в любой момент
4. Auditable — все grant/revoke логируются
5. Informed — пользователь знает, что он разрешает

Scopes: microphone, emotion_voice, reminiscence, health_twin,
        location, network, telemetry (всегда off).
"""
from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path

from aura.core import secure_db

CONSENT_DB = Path.home() / ".local/share/aura/consent.db"

# Все возможные scopes с описаниями (ISO 29184)
SCOPES = {
    "microphone": {
        "title": "Микрофон",
        "description": "Aura слушает голосовые команды.",
        "required": True,
        "gdpr_basis": "consent",
    },
    "emotion_voice": {
        "title": "Анализ эмоций по голосу",
        "description": "Aura определяет настроение по тону голоса.",
        "required": False,
        "gdpr_basis": "consent",
    },
    "reminiscence": {
        "title": "Автобиографическая память",
        "description": "Aura запоминает рассказы о прошлом.",
        "required": False,
        "gdpr_basis": "consent",
    },
    "health_twin": {
        "title": "Медицинский двойник",
        "description": "Aura ведёт граф здоровья: лекарства, визиты.",
        "required": False,
        "gdpr_basis": "consent",
    },
    "location": {
        "title": "Местоположение",
        "description": "Aura знает, где ты, для погоды и маршрутов.",
        "required": False,
        "gdpr_basis": "consent",
    },
    "network": {
        "title": "Сетевые запросы",
        "description": "Aura может обращаться к погоде, курсам, API.",
        "required": False,
        "gdpr_basis": "consent",
    },
    "telemetry": {
        "title": "Телеметрия",
        "description": "Отправка анонимной статистики в облако.",
        "required": False,
        "gdpr_basis": "consent",
        "always_off": True,  # никогда не включаем — принцип local-first
    },
}


def _ensure() -> None:
    CONSENT_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = secure_db.connect(CONSENT_DB, encrypt=True)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS consents (
            scope TEXT PRIMARY KEY,
            granted INTEGER NOT NULL,
            granted_at REAL,
            revoked_at REAL,
            version TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            iso TEXT NOT NULL,
            scope TEXT NOT NULL,
            action TEXT NOT NULL,
            version TEXT NOT NULL,
            note TEXT
        )
    """)
    conn.commit()
    conn.close()


def _log(scope: str, action: str, note: str = "") -> None:
    conn = secure_db.connect(CONSENT_DB, encrypt=True)
    conn.execute(
        "INSERT INTO audit_log (ts, iso, scope, action, version, note) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (time.time(), datetime.now(UTC).isoformat(),
         scope, action, "1.0", note),
    )
    conn.commit()
    conn.close()


def grant(scope: str, note: str = "") -> bool:
    """Дать согласие. Возвращает True при успехе."""
    if scope not in SCOPES:
        return False
    if SCOPES[scope].get("always_off"):
        return False  # нельзя включить
    _ensure()
    conn = secure_db.connect(CONSENT_DB, encrypt=True)
    conn.execute("""
        INSERT INTO consents (scope, granted, granted_at, version)
        VALUES (?, 1, ?, '1.0')
        ON CONFLICT(scope) DO UPDATE SET
            granted = 1,
            granted_at = excluded.granted_at,
            revoked_at = NULL
    """, (scope, time.time()))
    conn.commit()
    conn.close()
    _log(scope, "grant", note)
    return True


def revoke(scope: str, note: str = "") -> bool:
    """Отозвать согласие (GDPR Art.7(3))."""
    if scope not in SCOPES:
        return False
    if SCOPES[scope].get("required"):
        return False  # required нельзя отозвать, только удалить всё
    _ensure()
    conn = secure_db.connect(CONSENT_DB, encrypt=True)
    conn.execute("""
        UPDATE consents SET granted = 0, revoked_at = ? WHERE scope = ?
    """, (time.time(), scope))
    conn.commit()
    conn.close()
    _log(scope, "revoke", note)
    return True


def check(scope: str) -> bool:
    """Проверить, дано ли согласие."""
    if scope not in SCOPES:
        return False
    if SCOPES[scope].get("always_off"):
        return False
    _ensure()
    conn = secure_db.connect(CONSENT_DB, encrypt=True)
    row = conn.execute(
        "SELECT granted FROM consents WHERE scope = ?", (scope,)
    ).fetchone()
    conn.close()
    return bool(row and row[0])


def all_status() -> dict:
    """Статус всех scopes."""
    _ensure()
    conn = secure_db.connect(CONSENT_DB, encrypt=True)
    rows = conn.execute(
        "SELECT scope, granted FROM consents"
    ).fetchall()
    conn.close()
    granted_map = {s: bool(g) for s, g in rows}
    return {
        scope: {
            **info,
            "granted": granted_map.get(scope, False) and not info.get("always_off"),
        }
        for scope, info in SCOPES.items()
    }


def audit_log(limit: int = 100) -> list[dict]:
    """История grant/revoke."""
    _ensure()
    conn = secure_db.connect(CONSENT_DB, encrypt=True)
    rows = conn.execute(
        "SELECT ts, iso, scope, action, note FROM audit_log "
        "ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [
        {"ts": r[0], "iso": r[1], "scope": r[2],
         "action": r[3], "note": r[4]}
        for r in rows
    ]


def erase_all(reason: str = "") -> dict:
    """GDPR Art.17 — право на удаление. Удаляет все consent + log."""
    _ensure()
    conn = secure_db.connect(CONSENT_DB, encrypt=True)
    n_consents = conn.execute("DELETE FROM consents").rowcount
    n_logs = conn.execute("DELETE FROM audit_log").rowcount
    conn.commit()
    conn.close()
    # Записываем факт удаления (meta-log)
    _log("ALL", "erase", f"reason={reason}; consents={n_consents}; logs={n_logs}")
    return {"erased_consents": n_consents, "erased_logs": n_logs}


def require(scope: str) -> None:
    """Публичный API для агентов: raise если нет consent.

    Использование:
        consent.require("emotion_voice")
        # ... код, требующий согласия
    """
    if not check(scope):
        raise PermissionError(
            f"Consent not granted for scope '{scope}'. "
            f"Пользователь должен явно разрешить через 'aura consent grant {scope}'."
        )


def status() -> dict:
    """Публичный API: сводка."""
    return {
        "scopes_total": len(SCOPES),
        "granted": sum(1 for s in SCOPES if check(s)),
        "required": [s for s, i in SCOPES.items() if i.get("required")],
        "always_off": [s for s, i in SCOPES.items() if i.get("always_off")],
    }


__all__ = [
    "SCOPES",
    "all_status",
    "audit_log",
    "check",
    "erase_all",
    "grant",
    "require",
    "revoke",
    "status",
]
