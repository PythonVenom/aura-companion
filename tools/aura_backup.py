#!/usr/bin/env python3
"""T002: Backup RAG + journal + config. AURA_BACKUP_V1."""
import shutil
import tarfile
from datetime import datetime
from pathlib import Path

HOME = Path.home()
BACKUP_DIR = HOME / ".config" / "aura" / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = [
    HOME / ".cache" / "aura" / "chat_history.jsonl",
    HOME / ".cache" / "aura" / "chat_inbox.jsonl",
    HOME / ".cache" / "aura" / "aura_last_dialog.json",
    HOME / ".config" / "aura",
]

KEEP = 7  # хранить последние 7 бэкапов

def main():
    # AURA_BACKUP_THROTTLE_V1 — не чаще 1 раза в час
    import time
    last_file = sorted(BACKUP_DIR.glob("aura_backup_*.tar.gz"))
    if last_file:
        age_s = time.time() - last_file[-1].stat().st_mtime
        if age_s < 3600:
            print(f"[skip] последний backup {int(age_s)}с назад — ждём 3600")
            return 0
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = BACKUP_DIR / f"aura_backup_{stamp}.tar.gz"
    existing = []
    for t in TARGETS:
        if t.exists():
            existing.append(t)
        else:
            print(f"[skip] {t.name} — нет")
    if not existing:
        print("[FAIL] нечего бэкапить")
        return 1
    with tarfile.open(out, "w:gz") as tar:
        for t in existing:
            tar.add(t, arcname=t.name)
    print(f"[ok] backup → {out} ({out.stat().st_size // 1024} KB)")
    # Очистка старых
    backups = sorted(BACKUP_DIR.glob("aura_backup_*.tar.gz"))
    for old in backups[:-KEEP]:
        old.unlink()
        print(f"[cleanup] {old.name}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
