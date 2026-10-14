"""Boot report — POST (Power-On Self-Test) для AURA.

После старта система прогоняет диагностику и говорит:
- «Система в норме» — если всё ОК.
- «Обнаружено X проблем: [список]. Предпринял: [действия]. Жду внимания: [что]» — если что-то не так.

Наука:
- POST (IBM PC BIOS, 1981) — самопроверка при включении.
- Health Check Pattern (Release It!, Nygard 2007).
- Observability (SRE Book, Google 2016).

Формат JSON (для интеграции):
    {
      "ts": 1729...,
      "status": "ok" | "warnings" | "errors",
      "checks": [{"name": "doctor", "ok": true, "detail": "8/8"}],
      "problems": [...],
      "actions": [...],
      "attention": [...]
    }
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPORT_PATH = Path.home() / ".cache/aura/boot_report.json"
STRESS_DB = Path.home() / ".local/share/aura/stress.db"


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class BootReport:
    ts: float = field(default_factory=time.time)
    status: str = "ok"  # ok | warnings | errors
    checks: list[Check] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    attention: list[str] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append(Check(name=name, ok=ok, detail=detail))
        if not ok:
            self.problems.append(f"{name}: {detail}")

    def finalize(self) -> None:
        if not self.problems:
            self.status = "ok"
        elif len(self.problems) <= 2:
            self.status = "warnings"
        else:
            self.status = "errors"

    def to_dict(self) -> dict:
        return {
            "ts": self.ts,
            "status": self.status,
            "checks": [asdict(c) for c in self.checks],
            "problems": self.problems,
            "actions": self.actions,
            "attention": self.attention,
        }

    def save(self) -> None:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def to_text(self) -> str:
        """Человекочитаемый формат."""
        lines = ["🛸 AURA v8.2.0 — Boot Report", "━" * 40]
        for c in self.checks:
            mark = "✅" if c.ok else "❌"
            lines.append(f"{mark} {c.name}: {c.detail}")
        lines.append("━" * 40)

        if self.status == "ok":
            lines.append("📊 СТАТУС: СИСТЕМА В НОРМЕ")
        else:
            lines.append(f"⚠️ ОБНАРУЖЕНО {len(self.problems)} ПРОБЛЕМ:")
            for i, p in enumerate(self.problems, 1):
                lines.append(f"  {i}. {p}")
            if self.actions:
                lines.append("🛠 Предпринял:")
                for a in self.actions:
                    lines.append(f"  • {a}")
            if self.attention:
                lines.append("👁 Жду внимания:")
                for a in self.attention:
                    lines.append(f"  • {a}")
        return "\n".join(lines)


def _check_doctor() -> Check:
    """Проверка doctor (8 контрольных точек)."""
    try:
        r = subprocess.run(
            ["./venv/bin/python", "-m", "aura.cli", "doctor"],
            capture_output=True, text=True, timeout=60,
            cwd=str(Path(__file__).resolve().parents[2]),
        )
        out = r.stdout + r.stderr
        if "8/8 OK" in out:
            return Check("Doctor", True, "8/8 OK")
        # Ищем "X/8"
        import re
        m = re.search(r"(\d+)/8", out)
        detail = f"{m.group(1)}/8" if m else "unknown"
        return Check("Doctor", False, detail)
    except Exception as e:
        return Check("Doctor", False, f"error: {e}")


def _check_orchestrator() -> Check:
    """Проверка сборки оркестратора."""
    try:
        from aura.bootstrap import build_orchestrator
        orch = build_orchestrator()
        n = len(orch)
        ok = n >= 90
        return Check("Агентов", ok, str(n))
    except Exception as e:
        return Check("Агентов", False, f"error: {e}")


def _check_stress() -> Check:
    """Проверка soak-теста."""
    try:
        import sqlite3
        if not STRESS_DB.exists():
            return Check("Soak-test", False, "stress.db отсутствует")
        conn = sqlite3.connect(STRESS_DB)
        row = conn.execute(
            "SELECT COUNT(*), MAX(ts), (SELECT rss_mb FROM samples ORDER BY ts DESC LIMIT 1) FROM samples"
        ).fetchone()
        conn.close()
        n, last_ts, last_rss = row
        if not last_ts:
            return Check("Soak-test", False, "нет сэмплов")
        age_min = (time.time() - last_ts) / 60
        ok = age_min < 5  # сэмпл свежий
        detail = f"{n} сэмплов, RSS={last_rss:.0f} MB, {age_min:.0f} мин назад"
        return Check("Soak-test", ok, detail)
    except Exception as e:
        return Check("Soak-test", False, f"error: {e}")


def _check_eldercare() -> Check:
    """Проверка elder-care через test_elder.py."""
    try:
        r = subprocess.run(
            ["./venv/bin/python", "scripts/test_elder.py"],
            capture_output=True, text=True, timeout=120,
            cwd=str(Path(__file__).resolve().parents[2]),
        )
        out = r.stdout + r.stderr
        import re
        m = re.search(r"Итого: (\d+)/(\d+)", out)
        if m:
            got, total = int(m.group(1)), int(m.group(2))
            ok = got == total
            return Check("Elder-care", ok, f"{got}/{total}")
        return Check("Elder-care", False, "нет метрики")
    except Exception as e:
        return Check("Elder-care", False, f"error: {e}")


def _check_rag() -> Check:
    """Проверка готовности RAG."""
    try:
        from aura.agents.rag_memory import AgentRAGMemory
        r = AgentRAGMemory()
        ok = r.check_ready()
        detail = "загружен" if ok else "не загружен"
        return Check("RAG", ok, detail)
    except Exception as e:
        return Check("RAG", False, f"error: {e}")


def run_boot_report() -> BootReport:
    """Собрать полный boot-report."""
    rep = BootReport()
    rep.add("Doctor", _check_doctor().ok, _check_doctor().detail)
    rep.add("Агентов", _check_orchestrator().ok, _check_orchestrator().detail)
    rep.add("RAG", _check_rag().ok, _check_rag().detail)
    rep.add("Elder-care", _check_eldercare().ok, _check_eldercare().detail)
    rep.add("Soak-test", _check_stress().ok, _check_stress().detail)
    rep.finalize()
    rep.save()
    return rep


if __name__ == "__main__":
    report = run_boot_report()
    print(report.to_text())
