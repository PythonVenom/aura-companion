"""AgentRecon — обзор через aura_recon.py (ADR-068)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from aura.core.protocol import AgentResponse, BaseAgent

PROJECT = Path(__file__).parent.parent.parent

class AgentRecon(BaseAgent):
    name = "recon"
    MODULE_ALWAYS = True
    KEYWORDS = ("обзор", "recon", "диагностика", "статус системы", "покажи состояние")
    def can_handle(self, request):
        text = request.text.lower().strip()
        return any(kw in text for kw in self.KEYWORDS)
    async def handle(self, request):
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        try:
            r = subprocess.run(
                [sys.executable, str(PROJECT / "scripts/aura_recon.py"),
                 "base", "--out", "/tmp/aura_recon_latest.md", "--quiet"],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode != 0:
                return AgentResponse.ok(f"Recon: {r.stderr[:200]}", self.name)
            out = Path("/tmp/aura_recon_latest.md")
            if not out.exists():
                return AgentResponse.ok("Recon без файла", self.name)
            return AgentResponse.ok(
                f"Обзор готов:\n{out.read_text(encoding='utf-8')[:500]}\n/tmp/aura_recon_latest.md",
                self.name,
            )
        except Exception as e:
            return AgentResponse.ok(f"Recon: {e}", self.name)

__all__ = ["AgentRecon"]
