"""#147 AgentActions — LLM-диспетчер действий с файлами и email.

Наука:
- Tool Use (Schick 2023) — LLM выбирает инструмент
- Function Calling (OpenAI 2023) — структурированный вызов
- ReAct (Yao 2022) — reasoning перед действием

Зачем:
  «Найди файл отчёт.pdf и отправь маме по почте»
  → 1. Найти файл (shutil/glob)
  → 2. Отправить (AgentEmail)

Сейчас: простой parser (regex). Завтра: LLM-function-calling.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent
from aura.core.recall_log import record


class AgentActions(BaseAgent):
    """Действия с файлами и email по естественному языку."""

    name = "actions"

    TRIGGERS = (
        "найди файл", "найди документ", "отправь файл",
        "отправь по почте", "прикрепи файл",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text

        if "найди" in text.lower():
            return self._find_file(text)

        if "отправь" in text.lower():
            return await self._send_file(text)

        return AgentResponse.ok(
            "📝 Команды: 'найди файл X', 'отправь файл X по почте'",
            self.name,
        )

    def _find_file(self, text: str) -> AgentResponse:
        """Найти файл по имени (search в ~/)."""
        query = self._extract_file_name(text)
        if not query:
            return AgentResponse.ok("❌ Не поняла имя файла", self.name)

        home = Path.home()
        found = []
        for search_dir in [home / "Загрузки", home / "Documents",
                          home / "Downloads", home / "Desktop"]:
            if not search_dir.exists():
                continue
            try:
                for p in search_dir.rglob(f"*{query}*"):
                    found.append(p)
                    if len(found) >= 10:
                        break
            except (PermissionError, OSError):
                continue
            if len(found) >= 10:
                break

        if not found:
            return AgentResponse.ok(f"❌ Не найдено: {query}", self.name)

        try:
            record(self.name, "find_file", f"{query} → {len(found)}")
        except Exception:
            pass

        lines = [f"📁 Найдено {len(found)}:"]
        for p in found[:10]:
            size = p.stat().st_size // 1024
            lines.append(f"  • {p.name} ({size} КБ)")
        return AgentResponse.ok("\n".join(lines), self.name)

    async def _send_file(self, text: str) -> AgentResponse:
        """Отправить файл через AgentEmail."""
        query = self._extract_file_name(text)
        if not query:
            return AgentResponse.ok("❌ Не поняла какой файл отправить", self.name)

        # Найти файл
        home = Path.home()
        target = None
        for d in [home / "Загрузки", home / "Documents", home / "Downloads"]:
            if not d.exists():
                continue
            for p in d.rglob(f"*{query}*"):
                target = p
                break
            if target:
                break

        if not target:
            return AgentResponse.ok(f"❌ Файл не найден: {query}", self.name)

        # Отправить через AgentEmail
        try:
            from aura.agents.email_agent import AgentEmail
            email = AgentEmail()
            result = email._send(
                f"[Aura] Файл: {target.name}\n\n"
                f"Файл: {target}\nРазмер: {target.stat().st_size // 1024} КБ"
            )
            text_result = getattr(result, "text", str(result))
            record(self.name, "send_file", f"{target.name}")
            return AgentResponse.ok(
                f"📧 {text_result}\n📎 {target.name}",
                self.name,
            )
        except Exception as e:
            return AgentResponse.ok(f"❌ Не отправила: {e}", self.name)

    def _extract_file_name(self, text: str) -> str:
        """Извлечь имя файла из 'найди файл X' / 'отправь X по почте'."""
        patterns = [
            r"файл\s+[\"«]?([^\"»]+?)[\"»]?(?:\s+по почте|$)",
            r"документ\s+[\"«]?([^\"»]+?)[\"»]?(?:\s+по почте|$)",
            r"отправь\s+[\"«]?([^\"»]+?)[\"»]?\s+по почте",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return ""


__all__ = ["AgentActions"]
