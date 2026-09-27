"""Ротация логов для Ауры.

Раз в сутки переносит journal → файл, чистит старые (>7 дней).
"""
from __future__ import annotations

import gzip
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


LOG_DIR = Path.home() / "aura_private" / "logs"
KEEP_DAYS = 7


def export_today() -> Path:
    """Экспортировать журнал за сегодня в файл."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    out = LOG_DIR / f"aura-{today}.log"

    try:
        r = subprocess.run(
            ["journalctl", "--user", "-u", "aura.service",
             "--since", "today", "--no-pager"],
            capture_output=True, text=True, timeout=30)
        out.write_text(r.stdout, encoding="utf-8")
    except Exception as e:
        out.write_text(f"error: {e}\n", encoding="utf-8")
    return out


def gzip_old():
    """Сжать вчерашние логи."""
    cutoff = datetime.now() - timedelta(days=1)
    for f in LOG_DIR.glob("aura-*.log"):
        try:
            date_str = f.stem.replace("aura-", "")
            d = datetime.strptime(date_str, "%Y-%m-%d")
            if d.date() < cutoff.date():
                gz = f.with_suffix(".log.gz")
                if not gz.exists():
                    with open(f, "rb") as src, gzip.open(gz, "wb") as dst:
                        dst.write(src.read())
                    f.unlink()
        except Exception:
            pass


def purge_old():
    """Удалить >7 дней."""
    cutoff = datetime.now() - timedelta(days=KEEP_DAYS)
    for f in LOG_DIR.glob("aura-*.log.gz"):
        try:
            date_str = f.stem.replace("aura-", "").replace(".log", "")
            d = datetime.strptime(date_str, "%Y-%m-%d")
            if d.date() < cutoff.date():
                f.unlink()
        except Exception:
            pass


def run():
    f = export_today()
    gzip_old()
    purge_old()
    return f


if __name__ == "__main__":
    print(f"OK: {run()}")
