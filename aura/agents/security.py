"""
Агент безопасности (AgentSecurity).

Сканирование процессов на подозрительные утилиты + проверка открытых портов.

Мигрирован из agents/security.py (монолит, мёртвый по ADR-004).
Изменения:
- Контракт BaseAgent: can_handle / handle
- Логика НЕ менялась

Портирован как заготовка (Фаза 6). НЕ подключён к bootstrap.
См. ADR-004.
"""

from __future__ import annotations

import subprocess

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentSecurity(BaseAgent):
    """Проверка процессов и портов."""

    name = "security"

    SUSPICIOUS = ["nc", "nmap", "hydra", "sqlmap", "metasploit", "john", "aircrack"]

    KEYWORDS = (
        "проверь систему",
        "проверь процессы",
        "проверь порты",
        "открытые порты",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        cmd = request.text.lower()
        if "порт" in cmd:
            return AgentResponse.ok(text=self.check_ports(), agent_name=self.name)
        return AgentResponse.ok(text=self.scan_processes(), agent_name=self.name)

    def scan_processes(self) -> str:
        try:
            result = subprocess.run(
                ["ps", "aux"], capture_output=True, text=True, timeout=5
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
                return report
            return "✅ Система чиста"
        except Exception:
            return "❌ Ошибка сканирования"

    def check_ports(self) -> str:
        try:
            result = subprocess.run(
                ["ss", "-tuln"], capture_output=True, text=True, timeout=5
            )
            ports = []
            for line in result.stdout.split("\n"):
                if "LISTEN" not in line:
                    continue
                # Ищем часть с портом: есть ":" и цифры в конце.
                # Не по индексу — формат ss зависит от версии (Netid опционально).
                for part in line.split():
                    if ":" in part:
                        candidate = part.rsplit(":", 1)[-1]
                        if candidate.isdigit():
                            ports.append(candidate)
                            break
            if ports:
                return f"🔓 Открытые порты: {chr(44).join(ports[:10])}"
            return "🔒 Открытых портов нет"
        except Exception:
            return "❌ Не удалось проверить порты"


__all__ = ["AgentSecurity"]
