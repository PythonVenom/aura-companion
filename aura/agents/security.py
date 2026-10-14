"""#98 Security Agent — ClamAV + auditd + процессы + порты.

Расширение существующего AgentSecurity (был мёртвый по ADR-004).
Теперь: реальные сканы + notify(P0-P3) + подпись отчёта через ledger.

Наука:
- NIST SP 800-83 — Malware Incident Prevention
- NIST SP 800-61 — Incident Handling
- CIS Benchmark — аудит процессов и портов
"""
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from aura.core.ledger import sign as ledger_sign
from aura.core.notifications import NotifLevel, notify
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentSecurity(BaseAgent):
    """Проверка вирусов, процессов, портов, целостности системы."""

    name = "security"
    MODULE_ALWAYS = True

    SUSPICIOUS = ["nc", "nmap", "hydra", "sqlmap", "metasploit", "john", "aircrack"]

    # Пути для ClamAV-скана
    SCAN_PATHS = [
        Path.home() / "Загрузки",
        Path.home() / "Downloads",
        Path("/tmp"),
    ]

    KEYWORDS = (
        "проверь систему", "проверь процессы", "проверь порты", "открытые порты",
        "есть ли вирусы", "проверь на вирусы", "просканируй вирусы",
        "проверь целостность", "аудит системы", "полный отчёт безопасности",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        cmd = request.text.lower()
        if "полный отчёт" in cmd or "аудит системы" in cmd:
            return AgentResponse.ok(text=self.full_report(), agent_name=self.name)
        if "вирус" in cmd:
            return AgentResponse.ok(text=self.scan_viruses(), agent_name=self.name)
        if "целостност" in cmd:
            return AgentResponse.ok(text=self.check_integrity(), agent_name=self.name)
        if "порт" in cmd:
            return AgentResponse.ok(text=self.check_ports(), agent_name=self.name)
        return AgentResponse.ok(text=self.scan_processes(), agent_name=self.name)

    # ─── Процессы ───
    def scan_processes(self) -> str:
        try:
            result = subprocess.run(
                ["ps", "aux"], capture_output=True, text=True, timeout=5,
            )
            found = []
            for proc in result.stdout.split("\n"):
                for susp in self.SUSPICIOUS:
                    if susp in proc.lower():
                        found.append(proc.strip())
            if found:
                report = "🚨 Подозрительные процессы:\n"
                for p in found[:5]:
                    report += f"  - {p[:80]}\n"
                notify(NotifLevel.P1, "Aura Security", f"Найдено {len(found)} подозрительных процессов", agent=self.name)
                return report
            return "✅ Система чиста"
        except Exception:
            return "❌ Ошибка сканирования процессов"

    # ─── Порты ───
    def check_ports(self) -> str:
        try:
            result = subprocess.run(
                ["ss", "-tuln"], capture_output=True, text=True, timeout=5,
            )
            ports = []
            for line in result.stdout.split("\n"):
                if "LISTEN" not in line:
                    continue
                for part in line.split():
                    if ":" in part:
                        candidate = part.rsplit(":", 1)[-1]
                        if candidate.isdigit():
                            ports.append(candidate)
                            break
            if ports:
                return f"🔓 Открытые порты: {', '.join(ports[:10])}"
            return "🔒 Открытых портов нет"
        except Exception:
            return "❌ Не удалось проверить порты"

    # ─── Вирусы (ClamAV) ───
    def scan_viruses(self) -> str:
        if not shutil.which("clamscan"):
            return "⚠️ ClamAV не установлен: sudo pacman -S clamav"
        existing = [str(p) for p in self.SCAN_PATHS if p.exists()]
        if not existing:
            return "⚠️ Нет папок для сканирования"
        try:
            result = subprocess.run(
                ["clamscan", "--infected", "--no-summary", *existing],
                capture_output=True, text=True, timeout=120,
            )
            found = [l for l in result.stdout.split("\n") if "FOUND" in l]
            if found:
                notify(
                    NotifLevel.P0, "Aura Security",
                    f"🚨 Найдено {len(found)} вирусов!", agent=self.name,
                )
                return "🚨 Вирусы:\n" + "\n".join(f"  - {l[:80]}" for l in found[:5])
            return "✅ Вирусов не найдено"
        except subprocess.TimeoutExpired:
            return "⏱️ Скан ClamAV превысил 120 секунд"
        except Exception as e:
            return f"❌ Ошибка ClamAV: {e}"

    # ─── Целостность (auditd) ───
    def check_integrity(self) -> str:
        if not shutil.which("auditctl"):
            return "⚠️ auditd не установлен: sudo pacman -S audit"
        try:
            result = subprocess.run(
                ["auditctl", "-l"], capture_output=True, text=True, timeout=5,
            )
            rules = [l for l in result.stdout.split("\n") if l.strip()]
            if not rules:
                return "⚠️ Правила auditd не заданы"
            return f"🔍 auditd: {len(rules)} правил активно"
        except Exception as e:
            return f"❌ Ошибка auditd: {e}"

    # ─── Полный отчёт + подпись ───
    def full_report(self) -> str:
        """Агрегирует все проверки и подписывает через Ed25519."""
        report = {
            "ts": time.time(),
            "processes": self.scan_processes(),
            "ports": self.check_ports(),
            "viruses": self.scan_viruses(),
            "integrity": self.check_integrity(),
        }
        sig = ledger_sign(report, agent=self.name)
        report["signature"] = sig.hex()

        # Уведомление P1 (отчёт готов)
        notify(
            NotifLevel.P1, "Aura Security",
            f"Полный отчёт готов, подписан ({sig.hex()[:16]}...)",
            agent=self.name,
        )

        lines = [
            "🛡️ ПОЛНЫЙ ОТЧЁТ БЕЗОПАСНОСТИ",
            f"  Процессы:   {report['processes'].splitlines()[0][:60]}",  # type: ignore[attr-defined]
            f"  Порты:      {report['ports'][:60]}",  # type: ignore[index]
            f"  Вирусы:     {report['viruses'][:60]}",  # type: ignore[index]
            f"  Целостность: {report['integrity'][:60]}",  # type: ignore[index]
            f"  Подпись:    {sig.hex()[:32]}...",
        ]
        return "\n".join(lines)


__all__ = ["AgentSecurity"]
