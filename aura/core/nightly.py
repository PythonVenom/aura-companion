"""Nightly Report — ночной отчёт AURA (22:00).

Наука: Reflection (Schön 1983), Daily Review (Allen GTD).
Собирает события дня, эмоции, тренды.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path


def _events_today() -> list[dict]:
    """События за последние 24ч из blackboard."""
    try:
        from aura.core import blackboard as bb
        return bb.recent_alerts(window_sec=86400)
    except Exception:
        return []


def _tasks_today() -> list[dict]:
    try:
        from aura.core import blackboard as bb
        return bb.active_tasks()
    except Exception:
        return []


def _receipts_count() -> int:
    try:
        from aura.core.receipts import stats
        return stats()["receipts"]
    except Exception:
        return 0


def _stress_stats() -> dict:
    try:
        import sqlite3
        db = Path.home() / ".local/share/aura/stress.db"
        if not db.exists():
            return {}
        conn = sqlite3.connect(db)
        row = conn.execute(
            "SELECT COUNT(*), ROUND(MAX(rss_mb),1), ROUND(AVG(latency_ms),2) FROM samples"
        ).fetchone()
        conn.close()
        return {"samples": row[0], "rss_max": row[1], "latency_avg": row[2]}
    except Exception:
        return {}


def build() -> str:
    """Собрать ночной отчёт."""
    now = datetime.now()
    lines = [f"🌙 Ночной отчёт · {now.strftime('%Y-%m-%d %H:%M')}"]
    lines.append("─" * 50)

    events = _events_today()
    tasks = _tasks_today()
    receipts = _receipts_count()
    stress = _stress_stats()

    lines.append(f"📅 События за день: {len(events)}")
    if events:
        for e in events[-5:]:
            lines.append(f"   • {e.get('agent','?')}: {e.get('text','')[:40]}")

    lines.append(f"📋 Активных задач: {len(tasks)}")
    lines.append(f"🔐 Receipts: {receipts}")

    if stress:
        lines.append(f"📊 Soak: {stress.get('samples')} сэмплов, "
                     f"RSS max {stress.get('rss_max')} MB, "
                     f"latency {stress.get('latency_avg')} ms")

    try:
        from aura.core.emotion_evolution import get_state
        s = get_state()
        lines.append(f"😌 Эмоция дня: {s.dominant()}")
    except Exception:
        pass

    try:
        from aura.core.affinity import get_affinity
        a = get_affinity()
        lines.append(f"🤝 Отношения: {a.rank} (XP {a.xp})")
    except Exception:
        pass

    lines.append("─" * 50)
    lines.append("🦾 Дежурю дальше. Отдыхай, капитан.")
    return "\n".join(lines)


def main() -> None:
    print(build())


if __name__ == "__main__":
    main()


__all__ = ["build", "main"]
