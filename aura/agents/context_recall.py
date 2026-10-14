"""#141 AgentContextRecall — «что я делал N минут назад?»."""
from __future__ import annotations

import re

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent
from aura.core.recall_log import format_recall


class AgentContextRecall(BaseAgent):
    """Recall из журнала событий."""

    name = "context_recall"

    TRIGGERS = (
        "что я делал", "что было недавно", "напомни что",
        "что происходило", "последние события", "журнал событий",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()
        minutes = self._parse_minutes(t)
        return AgentResponse.ok(text=format_recall(minutes), agent_name=self.name)

    def _parse_minutes(self, text: str) -> int:
        m = re.search(r"(\d+)\s*мин", text)
        if m:
            return int(m.group(1))
        m = re.search(r"(\d+)\s*час", text)
        if m:
            return int(m.group(1)) * 60
        return 10  # default


__all__ = ["AgentContextRecall"]
