"""Knowledge — Аура читает файлы проекта.

Команды:
  «зачитай журнал»     → читает STORY.md
  «что в roadmap»      → читает ROADMAP
  «найди в файлах X»   → grep по aura_private/
  «прочитай файл X»    → читает любой файл

Наука: Nielsen 1993 (recognition over recall),
       Licklider 1960 (симбиоз).
"""
from __future__ import annotations

import contextlib
import re
from dataclasses import dataclass
from pathlib import Path

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse

SEARCH_ROOTS = [
    Path.home() / "aura_private",
    Path.home() / "aura_project" / "docs",
    Path.home() / "aura_project",
]


@dataclass
class Found:
    path: Path
    line: int
    text: str


def find_file(name: str) -> Path | None:
    """Найти файл по имени (fuzzy)."""
    name_l = name.lower().strip().replace(".md", "").replace(".", "")
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*.md"):
            stem = p.stem.lower().replace(".", "").replace("-", "")
            if name_l in stem or stem in name_l:
                return p
        for p in root.rglob("*.py"):
            if name_l == p.stem.lower():
                return p
    return None


def search_lines(query: str, limit: int = 10) -> list[Found]:
    """Поиск строк по ключевому слову."""
    q = query.lower().strip()
    if len(q) < 2:
        return []
    out: list[Found] = []
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for p in list(root.rglob("*.md")) + list(root.rglob("*.py")):
            # Исключаем мусор
            skip = (
                "__pycache__", ".git", "venv", "node_modules",
                ".mypy_cache", ".pytest_cache", ".ruff_cache",
            )
            if any(s in str(p) for s in skip):
                continue
            with contextlib.suppress(Exception):
                for i, line in enumerate(
                    p.read_text(encoding="utf-8").splitlines(), 1,
                ):
                    if q in line.lower():
                        out.append(Found(p, i, line.strip()[:120]))
                        if len(out) >= limit:
                            return out
    return out


def read_tail(path: Path, n: int = 20) -> str:
    """Последние N строк файла."""
    if not path.exists():
        return f"❌ Файл не найден: {path}"
    with contextlib.suppress(Exception):
        lines = path.read_text(encoding="utf-8").splitlines()
        return "\n".join(lines[-n:])
    return "❌ Ошибка чтения"


def read_full(path: Path, max_lines: int = 50) -> str:
    """Первые N строк файла."""
    if not path.exists():
        return f"❌ Файл не найден: {path}"
    with contextlib.suppress(Exception):
        lines = path.read_text(encoding="utf-8").splitlines()
        return "\n".join(lines[:max_lines])
    return "❌ Ошибка чтения"


class AgentKnowledge(MicroAgent):
    """Аура читает файлы проекта."""

    KEYWORDS = (
        "зачитай", "прочитай", "покажи файл",
        "что в журнале", "что в story", "бортовой журнал",
        "что в roadmap", "покажи roadmap",
        "найди в файлах", "поиск по проекту",
    )

    def __init__(self):
        super().__init__("knowledge", "Чтение файлов проекта")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        text = request.text.lower().strip()

        # 1. «зачитай журнал»
        if "журнал" in text or "story" in text:
            p = Path.home() / "aura_private" / "STORY.md"
            content = read_tail(p, 15)
            return AgentResponse.ok(
                f"📋 Последние записи:\n{content}",
                self.name,
            )

        # 2. «roadmap»
        if "roadmap" in text or "роадмап" in text:
            # Ищем в нескольких местах
            candidates = [
                Path.home() / "aura_private" / "ROADMAP-V2.md",
                Path.home() / "aura_private" / "ROADMAP.md",
                Path.home() / "aura_project" / "docs" / "ROADMAP.md",
                Path.home() / "aura_project" / "docs" / "internal" / "ROADMAP.md",
            ]
            for p in candidates:
                if p.exists():
                    return AgentResponse.ok(
                        f"📋 {p.name}:\n{read_full(p, 30)}",
                        self.name,
                    )
            # Fallback — глобальный поиск
            found = find_file("ROADMAP")
            if found:
                return AgentResponse.ok(
                    f"📋 {found.name}:\n{read_full(found, 30)}",
                    self.name,
                )
            return AgentResponse.ok("❌ ROADMAP не найден", self.name)

        # 3. «найди X в файлах»
        m = re.search(r"найди\s+(?:в\s+файлах\s+)?(.+)", text)
        if m:
            query = m.group(1).strip(" :,.-")
            found_lines = search_lines(query)
            if not found:
                return AgentResponse.ok(
                    f"🔍 «{query}» — не найдено",
                    self.name,
                )
            lines = [f"🔍 Найдено {len(found_lines)} строк:"]
            for f in found[:5]:
                rel = f.path.name
                lines.append(f"  {rel}:{f.line}  {f.text[:60]}")
            return AgentResponse.ok("\n".join(lines), self.name)

        # 4. «прочитай файл X»
        m = re.search(r"(?:прочитай|покажи)\s+(?:файл\s+)?(\S+)", text)
        if m:
            name = m.group(1).strip(" :,.-")
            p = find_file(name)
            if p is None:
                return AgentResponse.ok(
                    f"❌ Файл «{name}» не найден",
                    self.name,
                )
            return AgentResponse.ok(
                f"📄 {p.name}:\n{read_full(p, 30)}",
                self.name,
            )

        # 5. Справка
        return AgentResponse.ok(
            "📚 Что могу:\n"
            "  • зачитай журнал\n"
            "  • что в roadmap\n"
            "  • найди в файлах <текст>\n"
            "  • прочитай файл <имя>",
            self.name,
        )


__all__ = [
    "AgentKnowledge",
    "find_file", "read_full", "read_tail", "search_lines",
]
