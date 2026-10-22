"""Кодекс — Mass Effect слой.

Записи открываются по мере прогресса. Читаются из aura/lore/codex/*.md
с YAML frontmatter (title, chapter, unlock).

Наука: Brooks 1975 (кодекс — база знаний),
       Nielsen 1993 (recognition over recall),
       Campbell 1949 (записи = акты Hero's Journey).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CODEX_DIR = REPO / "aura" / "lore" / "codex"


@dataclass
class CodexEntry:
    """Одна запись кодекса."""

    slug: str
    title: str
    chapter: int
    unlock: str
    body: str
    tags: list[str] = field(default_factory=list)

    @property
    def unlocked_always(self) -> bool:
        return self.unlock in ("always", "", None)


_FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def _parse(path: Path) -> CodexEntry | None:
    """Распарсить .md с frontmatter. Без зависимостей (yaml не нужен)."""
    try:
        text = path.read_text(encoding="utf-8")
        m = _FRONT_RE.match(text)
        if not m:
            return None
        front, body = m.group(1), m.group(2).strip()
        meta: dict[str, str] = {}
        for line in front.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip("\"'")
        return CodexEntry(
            slug=path.stem,
            title=meta.get("title", path.stem),
            chapter=int(meta.get("chapter", 0)),
            unlock=meta.get("unlock", ""),
            body=body,
        )
    except Exception:
        return None


def list_entries() -> list[CodexEntry]:
    """Все записи, отсортированные по главе."""
    if not CODEX_DIR.exists():
        return []
    out = []
    for p in sorted(CODEX_DIR.rglob("*.md")):
        entry = _parse(p)
        if entry:
            out.append(entry)
    return sorted(out, key=lambda e: (e.chapter, e.slug))


def get_entry(slug: str) -> CodexEntry | None:
    for e in list_entries():
        if e.slug == slug:
            return e
    return None


def render_index() -> str:
    """ASCII-оглавление кодекса."""
    entries = list_entries()
    if not entries:
        return "📖 КОДЕКС ПУСТ. Записей пока нет."
    lines = ["📖 КОДЕКС AURA", ""]
    for e in entries:
        mark = "✓" if e.unlocked_always else "🔒"
        lines.append(f"  [{mark}] {e.slug:20} · гл.{e.chapter} · {e.title}")
    lines.append("")
    lines.append("Читать: aura codex <slug>")
    return "\n".join(lines)


def render_entry(slug: str) -> str:
    e = get_entry(slug)
    if not e:
        return f"❌ Запись '{slug}' не найдена"
    return f"📖 {e.title}\n{'─' * 40}\n{e.body}"
