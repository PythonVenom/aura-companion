"""#104 AgentSelfHeal — самодиагностика + рекомендации.

Наука:
- Wiener 1948 — cybernetics: feedback + control
- Kanfer 1970 — self-monitoring
- Deming 1950 — PDCA (Plan-Do-Check-Act)

Отличие от AgentSelfCheck:
- SelfCheck — что сломано? (feedback, 7 проверок оборудования)
- SelfHeal  — что делать? (control, 5 проверок + рекомендации)

БЕЗОПАСНОСТЬ: только диагностика + рекомендации.
Автономные действия (restart, kill) — по запросу, с подтверждением.
"""
from __future__ import annotations

import os
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentSelfHeal(BaseAgent):
    """Самодиагностика Aura с рекомендациями."""

    name = "self_heal"

    DIAGNOSE_KEYWORDS = (
        "почини себя", "что с тобой", "самодиагностика",
        "вылечи себя", "почему тормозишь", "почему долго думаешь",
        "что не так", "проверь здоровье",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.DIAGNOSE_KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        report = self.diagnose()
        return AgentResponse.ok(text=report, agent_name=self.name)

    # ─── Диагностика ───

    def diagnose(self) -> str:
        """Собрать отчёт по 5 проверкам."""
        checks = {
            "memory_mb": self._check_memory(),
            "media_state": self._check_media_state(),
            "agents_count": self._check_agents(),
            "ollama": self._check_ollama(),
            "llm_timeout": self._check_llm_timeout(),
        }
        issues = []
        if checks["memory_mb"] > 500:
            issues.append(f"⚠️ Память: {checks['memory_mb']:.0f} МБ (норма <500)")
        if checks["media_state"] == "vk":
            issues.append("⚠️ media_state залип на vk (сброшу?)")
        if checks["agents_count"] > 0 and checks["agents_count"] < 90:
            issues.append(f"⚠️ Агентов: {checks['agents_count']} (норма 96)")
        if not checks["ollama"]:
            issues.append("⚠️ Ollama не отвечает")
        if checks["llm_timeout"] > 10:
            issues.append(f"⚠️ LLM timeout: {checks['llm_timeout']}с (норма 8)")

        lines = ["🩺 САМОДИАГНОСТИКА AURA", ""]
        if not issues:
            lines.append("✅ Всё в порядке")
        else:
            lines.append(f"Найдено проблем: {len(issues)}")
            lines.extend(f"  {i}" for i in issues)
        lines.append("")
        lines.append(f"Память: {checks['memory_mb']:.0f} МБ · "
                     f"Агентов: {checks['agents_count']} · "
                     f"Ollama: {'✅' if checks['ollama'] else '❌'} · "
                     f"Timeout: {checks['llm_timeout']}с")
        return "\n".join(lines)

    # ─── Проверки ───

    def _check_memory(self) -> float:
        """RSS текущего процесса в МБ."""
        try:
            for line in Path("/proc/self/status").read_text().splitlines():
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024.0
        except Exception:
            pass
        return 0.0

    def _check_media_state(self) -> str:
        """Вернуть текущий media_state или 'none'."""
        try:
            from aura.agents import media_state
            return media_state.get_active() or "none"
        except Exception:
            return "unknown"

    def _check_agents(self) -> int:
        """Сколько агентов в orchestrator (если доступен)."""
        try:
            from aura.bootstrap import build_orchestrator
            orch = build_orchestrator()
            attr = "agents" if hasattr(orch, "agents") else "_agents"
            return len(getattr(orch, attr, {}))
        except Exception:
            return 0

    def _check_ollama(self) -> bool:
        """Ollama отвечает на /api/tags?"""
        try:
            import urllib.request
            with urllib.request.urlopen(
                "http://localhost:11434/api/tags", timeout=2
            ) as r:
                return r.status == 200
        except Exception:
            return False

    def _check_llm_timeout(self) -> int:
        """Текущий AURA_LLM_TIMEOUT (env или default 8)."""
        try:
            return int(os.environ.get("AURA_LLM_TIMEOUT", "8"))
        except (ValueError, TypeError):
            return 8


__all__ = ["AgentSelfHeal"]
