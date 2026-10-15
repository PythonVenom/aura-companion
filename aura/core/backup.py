"""Backup — авто-бэкап критичных данных AURA.

Наука: Backup 3-2-1 Rule (Peter Krogh), SRE Book.
Стратегия: критичные БД + JSON в tar.gz, ротация 7 дней.
"""
from __future__ import annotations

import tarfile
from datetime import datetime
from pathlib import Path

BACKUP_DIR = Path.home() / ".local" / "share" / "aura" / "backups"
CRITICAL = [
    "~/.local/share/aura/stress.db",
    "~/.local/share/aura/recall.db",
    "~/.local/share/aura/meds.db",
    "~/.config/aura/settings.json",
    "~/.cache/aura/blackboard.json",
    "~/.cache/aura/affinity.json",
    "~/.cache/aura/receipts.jsonl",
]
MAX_BACKUPS = 7


def _resolve(paths: list[str]) -> list[Path]:
    out = []
    for p in paths:
        pp = Path(p).expanduser()
        if pp.exists():
            out.append(pp)
    return out


def create() -> Path:
    """Создать бэкап. Возврат: путь к архиву."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = BACKUP_DIR / f"aura-backup-{stamp}.tar.gz"
    files = _resolve(CRITICAL)
    with tarfile.open(archive, "w:gz") as tar:
        for f in files:
            try:
                tar.add(f, arcname=f.name)
            except Exception:
                pass
    return archive


def rotate(max_count: int = MAX_BACKUPS) -> int:
    """Оставить только N последних бэкапов. Возврат: сколько удалено."""
    backups = sorted(BACKUP_DIR.glob("aura-backup-*.tar.gz"), reverse=True)
    deleted = 0
    for old in backups[max_count:]:
        try:
            old.unlink()
            deleted += 1
        except Exception:
            pass
    return deleted


def stats() -> dict:
    if not BACKUP_DIR.exists():
        return {"count": 0, "latest": None, "size_mb": 0}
    backups = sorted(BACKUP_DIR.glob("aura-backup-*.tar.gz"), reverse=True)
    total = sum(b.stat().st_size for b in backups) / (1024 * 1024)
    return {
        "count": len(backups),
        "latest": str(backups[0]) if backups else None,
        "size_mb": round(total, 2),
    }


def main() -> None:
    archive = create()
    deleted = rotate()
    print(f"✅ Backup: {archive}")
    print(f"   Удалено старых: {deleted}")
    print(f"   Stats: {stats()}")


if __name__ == "__main__":
    main()


__all__ = ["BACKUP_DIR", "create", "main", "rotate", "stats"]
