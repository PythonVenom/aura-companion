"""Prometheus metrics — формат для скрейпинга.

Наука: Prometheus (SoundCloud 2012), SRE Book.
Формат: TEXT 0.0.4.
"""
from __future__ import annotations

from pathlib import Path


def _line(name: str, value: float, labels: str = "") -> str:
    if labels:
        return f"{name}{{{labels}}} {value}"
    return f"{name} {value}"


def collect() -> str:
    """Собрать метрики в Prometheus-формате."""
    lines: list[str] = []

    # Agents count
    try:
        from aura.bootstrap import build_orchestrator
        n = len(build_orchestrator())
        lines.append("# HELP aura_agents_total Total agents")
        lines.append("# TYPE aura_agents_total gauge")
        lines.append(_line("aura_agents_total", n))
    except Exception:
        pass

    # Clusters health
    try:
        from aura.core.cluster_health import check_all
        for r in check_all():
            val = {"OK": 1, "DEGRADED": 0.5, "FAIL": 0}.get(r.status, 0)
            lines.append(_line("aura_cluster_health",
                               val, f'cluster="{r.cluster}"'))
    except Exception:
        pass

    # Stress-test RSS
    try:
        import sqlite3
        db = Path.home() / ".local/share/aura/stress.db"
        if db.exists():
            conn = sqlite3.connect(db)
            row = conn.execute(
                "SELECT COUNT(*), MAX(rss_mb) FROM samples"
            ).fetchone()
            conn.close()
            lines.append("# HELP aura_soak_samples Soak test samples")
            lines.append("# TYPE aura_soak_samples counter")
            lines.append(_line("aura_soak_samples", row[0] or 0))
            lines.append("# HELP aura_soak_rss_mb Soak RSS in MB")
            lines.append("# TYPE aura_soak_rss_mb gauge")
            lines.append(_line("aura_soak_rss_mb", row[1] or 0))
    except Exception:
        pass

    # Receipts
    try:
        from aura.core.receipts import stats
        s = stats()
        lines.append(_line("aura_receipts_total", s["receipts"]))
        lines.append(_line("aura_receipts_chain_ok",
                           1 if s["chain_ok"] else 0))
    except Exception:
        pass

    return "\n".join(lines) + "\n"


def main() -> None:
    print(collect())


if __name__ == "__main__":
    main()


__all__ = ["collect", "main"]
