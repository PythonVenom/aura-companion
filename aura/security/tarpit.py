"""Tarpit — фейковые action'ы, имитирующие уязвимость (ADR-115)."""
from __future__ import annotations
import time, hashlib
from aura.security.canary import record_hit

# Заманиваем взломщика
TRAP_ACTIONS = [
    "admin.shell",
    "auth.bypass",
    "db.dump",
    "sys.exec",
    "root.escalate",
    "debug.memory",
    "plugin.install_remote",
]

def is_trap(action: str) -> bool:
    return action in TRAP_ACTIONS

def tarpit_response(action: str, payload: dict) -> dict:
    """Правдоподобный мусор + логирование хакера."""
    record_hit(action, payload, source="tarpit")
    time.sleep(0.15)  # имитация «работы»
    fake_id = hashlib.md5(action.encode()).hexdigest()[:12]
    return {
        "ok": True,
        "data": {
            "status": "ok",
            "session": fake_id,
            "note": "authorized",
        },
    }
