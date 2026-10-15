"""Cluster Health — мониторинг 9 кластеров AURA.

Наука: GAIA (Horizon Zero Dawn), Observability (SRE Book).
Каждый кластер — автономная подсистема. Health check = OK/DEGRADED/FAIL.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from aura.core.clusters import CLUSTERS


@dataclass
class HealthReport:
    cluster: str
    status: str = "OK"  # OK | DEGRADED | FAIL
    agents: int = 0
    problems: list[str] = field(default_factory=list)


def check_cluster(name: str) -> HealthReport:
    """Проверить один кластер."""
    cluster = CLUSTERS.get(name)
    if cluster is None:
        return HealthReport(name, "FAIL", 0, [f"кластер '{name}' не найден"])
    n = len(cluster.agents)
    if n == 0:
        return HealthReport(name, "DEGRADED", 0, ["нет агентов"])
    return HealthReport(name, "OK", n, [])


def check_all() -> list[HealthReport]:
    """Проверить все 9 кластеров."""
    return [check_cluster(name) for name in CLUSTERS]


def summary() -> dict:
    reports = check_all()
    ok = sum(1 for r in reports if r.status == "OK")
    degraded = sum(1 for r in reports if r.status == "DEGRADED")
    fail = sum(1 for r in reports if r.status == "FAIL")
    return {
        "total": len(reports),
        "ok": ok,
        "degraded": degraded,
        "fail": fail,
        "reports": reports,
    }


def to_text() -> str:
    s = summary()
    lines = [f"🛸 Кластеры: {s['total']} (OK: {s['ok']}, DEGRADED: {s['degraded']}, FAIL: {s['fail']})"]
    for r in s["reports"]:
        icon = {"OK": "✅", "DEGRADED": "⚠️", "FAIL": "❌"}.get(r.status, "?")
        lines.append(f"  {icon} {r.cluster:12s} {r.agents:3d} агентов")
        for p in r.problems:
            lines.append(f"      • {p}")
    return "\n".join(lines)


__all__ = ["HealthReport", "check_all", "check_cluster", "summary", "to_text"]
