"""Mesh — синхронизация AURA между устройствами (N.E.K.O. multi-device).

Наука: CRDT (Shapiro 2011), ZeroMQ bridge.
Простейший вариант: экспорт/импорт состояния через shared-папку.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

MESH_DIR = Path.home() / ".local" / "share" / "aura" / "mesh"
STATE_DIR = Path.home() / ".cache" / "aura"


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def export_state(device: str = "local") -> Path:
    """Экспорт состояния в mesh-папку."""
    MESH_DIR.mkdir(parents=True, exist_ok=True)
    target = MESH_DIR / f"{device}-{_stamp()}.json"
    state = {}
    for name in ("blackboard.json", "affinity.json"):
        src = STATE_DIR / name
        if src.exists():
            try:
                state[name] = json.loads(src.read_text(encoding="utf-8"))
            except Exception:
                pass
    target.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def list_snapshots() -> list[Path]:
    """Список экспортов."""
    if not MESH_DIR.exists():
        return []
    return sorted(MESH_DIR.glob("*.json"), reverse=True)


def import_latest() -> dict | None:
    """Импортировать последний экспорт."""
    snaps = list_snapshots()
    if not snaps:
        return None
    try:
        return json.loads(snaps[0].read_text(encoding="utf-8"))
    except Exception:
        return None


def merge_from(source: Path) -> int:
    """Слить состояние из источника. Возврат: сколько файлов обновлено."""
    if not source.exists():
        return 0
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except Exception:
        return 0
    n = 0
    for name, content in data.items():
        target = STATE_DIR / name
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(content, ensure_ascii=False, indent=2),
                              encoding="utf-8")
            n += 1
        except Exception:
            pass
    return n


def stats() -> dict:
    return {
        "dir": str(MESH_DIR),
        "snapshots": len(list_snapshots()),
        "latest": str(list_snapshots()[0]) if list_snapshots() else None,
    }


__all__ = ["export_state", "import_latest", "list_snapshots", "merge_from", "stats"]
