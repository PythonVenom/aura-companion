"""#143 AgentRules — управление IFTTT-правилами."""
from __future__ import annotations

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent
from aura.core.rules import (
    format_rules,
)
from aura.core.rules import (
    remove as remove_rule,
)


class AgentRules(BaseAgent):
    name = "rules"

    TRIGGERS = (
        "правило", "правила", "список правил",
        "добавь правило", "удали правило",
        "если", "ifttt",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()

        if "список" in t or "какие правила" in t:
            return AgentResponse.ok(format_rules(), self.name)

        if "удали правило" in t:
            name = self._extract_name(request.text)
            if name and remove_rule(name):
                return AgentResponse.ok(f"🗑️ Удалено: {name}", self.name)
            return AgentResponse.ok(f"❌ Не найдено: {name}", self.name)

        if "добавь правило" in t:
            # Формат: "добавь правило NAME: если EVENT то ACTION"
            return AgentResponse.ok(
                "📝 Формат: 'добавь правило NAME: если EVENT то ACTION'\n"
                "   Или отредактируй ~/.config/aura/rules.json напрямую.",
                self.name,
            )

        return AgentResponse.ok(format_rules(), self.name)

    def _extract_name(self, text: str) -> str:
        import re
        m = re.search(r"правило\s+[\"«]?([^\"»]+?)[\"»]?\s*$", text)
        return m.group(1).strip() if m else ""


__all__ = ["AgentRules"]
