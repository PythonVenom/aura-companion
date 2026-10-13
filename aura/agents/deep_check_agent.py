"""Deep Check Agent — «Аура, проверь систему»."""

from __future__ import annotations

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


class AgentDeepCheck(MicroAgent):
    """Полная проверка всех систем Aura."""

    KEYWORDS = (
        # Только явные про Ауру (не про ОС/безопасность)
        "проверь ауру", "проверь себя аура",
        "диагностика ауры", "глубокая проверка",
        "глубокая диагностика", "все системы ауры",
        "все ли в порядке с аурой",
    )

    def __init__(self):
        super().__init__("deep_check", "Глубокая проверка систем")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        try:
            from aura.system.deep_check import render_report, run_deep_check
            report = run_deep_check()
            text = render_report(verbose=True)
            # Голосом — краткий итог
            if report.all_ok:
                voice = (f"Глубокая проверка завершена. "
                         f"Все {report.total} систем в норме.")
            else:
                fails = ", ".join(r.name for r in report.failures()[:3])
                voice = (f"Проверка завершена. "
                         f"{report.ok_count} из {report.total} в норме. "
                         f"Проблемы: {fails}.")
            return AgentResponse.ok(
                f"{text}\n\n🔊 Голос: {voice}",
                self.name,
            )
        except Exception as e:
            return AgentResponse.ok(
                f"❌ Проверка не удалась: {e}",
                self.name,
            )


__all__ = ["AgentDeepCheck"]
