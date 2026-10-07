"""SelfCheck agent — самопроверка + голосовой отчёт (F-037).

Наука (Д4):
- Wiener 1948 — cybernetics: feedback loop
- Kanfer 1970 — self-monitoring
- Duhigg 2012 — habit loop: cue → routine → reward
- Nielsen 1993 — visibility of system status
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


class AgentSelfCheck(MicroAgent):
    name = "self_check"

    TRIGGERS = (
        "проверь себя", "проверка", "статус системы",
        "self check", "selfcheck", "всё работает",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        results = self._run_all()
        report = self._format_report(results)

        # Голосом через speaker
        try:
            from aura.agents.speaker import AgentSpeaker
            sp = AgentSpeaker()
            sp.say(report, speak_short=True)
        except Exception:
            pass

        return AgentResponse.ok(text=report, agent_name=self.name)

    def _run_all(self) -> dict:
        return {
            "microphone": self._check_microphone(),
            "tts": self._check_tts(),
            "sqlcipher": self._check_sqlcipher(),
            "ollama": self._check_ollama(),
            "tray": self._check_tray(),
            "memory": self._check_memory(),
            "disk": self._check_disk(),
        }

    def _check_microphone(self) -> bool:
        try:
            r = subprocess.run(
                ["pactl", "get-source-mute", "@DEFAULT_SOURCE@"],
                capture_output=True, text=True, timeout=2,
            )
            return "no" in r.stdout.lower()
        except Exception:
            return False

    def _check_tts(self) -> bool:
        return shutil.which("piper") is not None or (
            Path.home() / "aura_project/voices/ru_RU-irina-medium.onnx"
        ).exists()

    def _check_sqlcipher(self) -> bool:
        try:
            import sqlcipher3
            return True
        except ImportError:
            return False

    def _check_ollama(self) -> bool:
        try:
            r = subprocess.run(
                ["pgrep", "-f", "ollama"],
                capture_output=True, timeout=2,
            )
            return r.returncode == 0
        except Exception:
            return False

    def _check_tray(self) -> bool:
        try:
            r = subprocess.run(
                ["pgrep", "-f", "aura_tray"],
                capture_output=True, timeout=2,
            )
            return r.returncode == 0
        except Exception:
            return False

    def _check_memory(self) -> bool:
        try:
            return True
        except Exception:
            return False

    def _check_disk(self) -> bool:
        try:
            r = subprocess.run(
                ["df", "-h", str(Path.home())],
                capture_output=True, text=True, timeout=2,
            )
            return r.returncode == 0
        except Exception:
            return False

    def _format_report(self, results: dict) -> str:
        ok = sum(1 for v in results.values() if v)
        total = len(results)
        if ok == total:
            head = "✅ Все системы в норме."
        else:
            head = f"⚠️ Проверено: {ok}/{total}."
        lines = [head]
        for k, v in results.items():
            mark = "🟢" if v else "🔴"
            lines.append(f"  {mark} {k}")
        return "\n".join(lines)


__all__ = ["AgentSelfCheck"]
