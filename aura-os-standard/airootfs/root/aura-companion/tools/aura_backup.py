#!/usr/bin/env python3
"""T002: Backup RAG + journal + config + state (AURA_BACKUP_V2).

Наука: Krogh 2009 — правило 3-2-1:
  3 копии данных
  2 разных носителя
  1 offsite

Сейчас:
  1) ~/.config/aura/backups/    (nvme0n1p2)
  2) /mnt/aura_hdd/backups/     (sdb2 — другой носитель)
  3) (опционально) rclone → облако
"""
import shutil
import tarfile
from datetime import datetime
from pathlib import Path

HOME = Path.home()
BACKUP_DIR = HOME / ".config" / "aura" / "backups"
OFFSITE_DIR = Path("/mnt/aura_hdd/backups/aura")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# F-BACKUP-V2: расширено (RAG, state, journal, logs)
TARGETS = [
    HOME / ".cache" / "aura" / "chat_history.jsonl",
    HOME / ".cache" / "aura" / "chat_inbox.jsonl",
    HOME / ".cache" / "aura" / "aura_last_dialog.json",
    HOME / ".cache" / "aura" / "logs.jsonl",           # НОВОЕ
    HOME / ".cache" / "aura" / "JOURNAL.md",            # НОВОЕ
    HOME / ".cache" / "aura" / "memory_registry.json",  # НОВОЕ
    HOME / ".cache" / "aura" / "chroma",                # НОВОЕ (RAG)
    HOME / ".config" / "aura" / "state.db",             # НОВОЕ (игра)
    HOME / ".config" / "aura" / "modules.toml",         # НОВОЕ
    HOME / "aura-companion" / "config" / "identity.yaml",  # НОВОЕ (путь верный)
]

KEEP = 7  # локально
KEEP_OFFSITE = 30  # offsite дольше


def _make_archive(targets, out_path: Path) -> int:
    """Создать tar.gz. Вернуть размер в KB."""
    with tarfile.open(out_path, "w:gz") as tar:
        for t in targets:
            try:
                tar.add(t, arcname=t.name)
            except Exception as e:
                print(f"[warn] не упакован {t}: {e}")
    return out_path.stat().st_size // 1024


def _rotate(directory: Path, pattern: str, keep: int) -> None:
    """Удалить старые архивы, оставить N."""
    backups = sorted(directory.glob(pattern))
    for old in backups[:-keep]:
        try:
            old.unlink()
            print(f"[cleanup] {old.name}")
        except Exception:
            pass


def main() -> int:
    # Throttle: не чаще 1 раза в час
    import time
    last_file = sorted(BACKUP_DIR.glob("aura_backup_*.tar.gz"))
    if last_file:
        age_s = time.time() - last_file[-1].stat().st_mtime
        if age_s < 3600:
            print(f"[skip] последний backup {int(age_s)}с назад — ждём 3600")
            return 0

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    existing = [t for t in TARGETS if t.exists()]
    if not existing:
        print("[FAIL] нечего бэкапить")
        return 1

    missing = [t.name for t in TARGETS if not t.exists()]
    if missing:
        print(f"[skip] нет: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}")

    # === 1. Локальный бэкап ===
    out = BACKUP_DIR / f"aura_backup_{stamp}.tar.gz"
    size = _make_archive(existing, out)
    print(f"[ok] local → {out} ({size} KB)")

    # === 2. Offsite (другой носитель) ===
    try:
        OFFSITE_DIR.mkdir(parents=True, exist_ok=True)
        off = OFFSITE_DIR / f"aura_backup_{stamp}.tar.gz"
        size_off = _make_archive(existing, off)
        print(f"[ok] offsite → {off} ({size_off} KB)")
        _rotate(OFFSITE_DIR, "aura_backup_*.tar.gz", KEEP_OFFSITE)
    except Exception as e:
        print(f"[warn] offsite пропущен: {e}")

    # === 3. Очистка локальных ===
    _rotate(BACKUP_DIR, "aura_backup_*.tar.gz", KEEP)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
