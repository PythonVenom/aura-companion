"""Анализ metrics.csv после 24-часового прогона.

Использование:
    python scripts/stability_report.py /tmp/aura_stability/metrics.csv
"""
import csv
import sys
from pathlib import Path


def analyze(csv_path: str) -> dict:
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        return {"error": "CSV пуст"}

    def _stat(key):
        vals = [float(r[key]) for r in rows if r.get(key)]
        if not vals:
            return {"min": 0, "max": 0, "avg": 0}
        return {
            "min": min(vals),
            "max": max(vals),
            "avg": sum(vals) / len(vals),
        }

    return {
        "iterations": len(rows),
        "rss_mb": _stat("rss_mb"),
        "cpu_pct": _stat("cpu_pct"),
        "errors_total": sum(int(r["errors_5min"]) for r in rows if r.get("errors_5min")),
        "restarts_max": max(int(r["restarts"]) for r in rows if r.get("restarts")),
        "service_active_pct": 100.0 * sum(
            1 for r in rows if r.get("service") == "active"
        ) / len(rows),
    }


def format_report(stats: dict) -> str:
    lines = ["📊 Stability Report", "=" * 40]
    lines.append(f"Итераций: {stats['iterations']}")
    lines.append(f"Service active: {stats['service_active_pct']:.1f}%")
    lines.append(f"RSS (MB): min={stats['rss_mb']['min']:.0f} "
                 f"max={stats['rss_mb']['max']:.0f} "
                 f"avg={stats['rss_mb']['avg']:.0f}")
    lines.append(f"CPU (%): min={stats['cpu_pct']['min']:.1f} "
                 f"max={stats['cpu_pct']['max']:.1f} "
                 f"avg={stats['cpu_pct']['avg']:.1f}")
    lines.append(f"Ошибок (сумма): {stats['errors_total']}")
    lines.append(f"Рестартов: {stats['restarts_max']}")

    # Оценка
    ok = (
        stats["service_active_pct"] >= 99.0
        and stats["restarts_max"] == 0
        and stats["rss_mb"]["max"] < 2048
    )
    lines.append("=" * 40)
    lines.append("✅ PASS" if ok else "⚠️  ATTENTION")
    return "
".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python scripts/stability_report.py <csv>")
        sys.exit(1)
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"❌ Не найден: {path}")
        sys.exit(1)
    stats = analyze(str(path))
    print(format_report(stats))
