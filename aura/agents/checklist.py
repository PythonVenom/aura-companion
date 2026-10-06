"""AgentChecklist: голосовое управление чек-листом.

Формат: markdown `- [ ] пункт` (незакрытый) / `- [x] пункт` (закрытый).
Источник: ~/aura_private/CHECKLIST.md
"""
from __future__ import annotations

import re
from pathlib import Path

from aura.agents.base import MicroAgent


CHECKLIST_PATH = Path.home() / "aura_private" / "CHECKLIST.md"
_UNCHECKED = re.compile(r"^\s*-\s*\[\s*\]\s*(.+?)\s*$")
_CHECKED = re.compile(r"^\s*-\s*\[[xX]\]\s*(.+?)\s*$")


def read_today() -> list:
    """Вернуть список незакрытых пунктов."""
    if not CHECKLIST_PATH.exists():
        return []
    out = []
    for line in CHECKLIST_PATH.read_text(encoding="utf-8").splitlines():
        m = _UNCHECKED.match(line)
        if m:
            out.append(m.group(1))
    return out


def add_item(text: str) -> bool:
    """Добавить пункт в конец файла (в раздел 🔴 Критично если есть)."""
    if not text:
        return False
    text = text.strip()
    if not CHECKLIST_PATH.exists():
        CHECKLIST_PATH.write_text(f"# Чек-лист\n\n## 🔴 Критично\n- [ ] {text}\n",
                                  encoding="utf-8")
        return True
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    # Вставляем после заголовка «## 🔴 Критично» (первая пустая строка после)
    marker = "## 🔴 Критично"
    idx = content.find(marker)
    if idx >= 0:
        after = content.find("\n", idx + len(marker))
        if after > 0:
            content = content[:after + 1] + f"- [ ] {text}\n" + content[after + 1:]
    else:
        content = content.rstrip() + f"\n\n- [ ] {text}\n"
    CHECKLIST_PATH.write_text(content, encoding="utf-8")
    return True


def complete_item(query: str) -> bool:
    """Отметить пункт выполненным. Поиск по подстроке (case-insensitive)."""
    if not query or not CHECKLIST_PATH.exists():
        return False
    q = query.lower().strip()
    lines = CHECKLIST_PATH.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        m = _UNCHECKED.match(line)
        if m and q in m.group(1).lower():
            indent = line[:len(line) - len(line.lstrip())]
            lines[i] = f"{indent}- [x] {m.group(1)}"
            CHECKLIST_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return True
    return False


def summary() -> str:
    """Голосовая сводка. Пустая строка если нечего."""
    items = read_today()
    if not items:
        return ""
    if len(items) == 1:
        return f"В чек-листе: {items[0]}"
    head = ", ".join(items[:3])
    tail = "" if len(items) <= 3 else f" и ещё {len(items) - 3}"
    return f"В чек-листе {len(items)}: {head}{tail}"


# === AgentChecklist: BaseAgent обёртка ===

from aura.core.protocol import AgentRequest, AgentResponse


class AgentChecklist(MicroAgent):
    """Голосовое управление чек-листом."""

    KEYWORDS = (
        # ASR глотает окончания: «чек-лист» → «чек лит»/«чек лист»
        "чек-лист", "чеклист", "чек лист", "чек лит", "чек-литс", "чеклит",
        "чеклист", "чек ли",
        "что осталось", "что в чек", "что по чек",
        "добавь в чек", "запиши в чек",
        "выполнил", "выполнено", "готово в чек", "готово по чек",
    )

    def __init__(self):
        super().__init__("checklist", "Чек-лист")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        text = request.text
        low = text.lower().strip()

        # «выполнил X» / «готово X в чек»
        for kw in ("выполнил ", "выполнено ", "готово "):
            if kw in low:
                idx = low.index(kw) + len(kw)
                item = text[idx:].strip(" .,!?:")
                item = item.replace("в чек-листе", "").replace("в чек", "").strip()
                if item and complete_item(item):
                    return AgentResponse.ok(f"✅ Отметила: {item}", self.name)
                return AgentResponse.ok(f"❌ Не нашла: {item}", self.name)

        # «добавь в чек-лист: X» / «запиши в чек: X»
        for kw in ("добавь в чек-лист", "добавь в чеклист", "добавь в чек",
                   "запиши в чек-лист", "запиши в чеклист", "запиши в чек"):
            if kw in low:
                idx = low.index(kw) + len(kw)
                item = text[idx:].strip(" :.,!?")
                if item:
                    add_item(item)
                    return AgentResponse.ok(f"✅ Добавила: {item}", self.name)
                return AgentResponse.ok("Что добавить?", self.name)

        # «что осталось» / «чек-лист» → сводка
        s = summary()
        if s:
            return AgentResponse.ok(s, self.name)
        return AgentResponse.ok("Чек-лист пуст 🎉", self.name)



__all__ = [
    "read_today", "add_item", "complete_item", "summary",
    "CHECKLIST_PATH", "AgentChecklist",
]
