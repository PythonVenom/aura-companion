"""Logbook — бортовой журнал Aura (ADR-084).

Не лог действий. Жизненный контекст:
- Что делали (events)
- Что решили (decisions)
- Где остановились (unresolved)
- Настроение дня (mood)

Формат: ~/.cache/aura/logbook/
- YYYY-MM-DD.jsonl (машинный, для LLM)
- YYYY-MM-DD.md (человекочитаемый)
- index.db (SQLite — позже)
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path

DEFAULT_ROOT = Path.home() / ".cache/aura/logbook"


@dataclass
class LogEntry:
    kind: str           # event, decision, unresolved, mood
    text: str
    meta: dict = field(default_factory=dict)
    ts: float = field(default_factory=time.time)


class Logbook:
    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else DEFAULT_ROOT
        self.root.mkdir(parents=True, exist_ok=True)

    def _today_str(self) -> str:
        return date.today().isoformat()

    def _jsonl_path(self) -> Path:
        return self.root / f"{self._today_str()}.jsonl"

    def _md_path(self) -> Path:
        return self.root / f"{self._today_str()}.md"

    def _append(self, entry: LogEntry) -> None:
        p = self._jsonl_path()
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

    def event(self, kind: str, text: str, meta: dict | None = None) -> None:
        self._append(LogEntry("event", f"[{kind}] {text}", meta or {}))

    def decision(self, key: str, why: str, adr: str | None = None) -> None:
        meta = {"adr": adr} if adr else {}
        self._append(LogEntry("decision", f"{key}: {why}", meta))

    def unresolved(self, what: str, status: str = "") -> None:
        self._append(LogEntry("unresolved", what, {"status": status}))

    def mood(self, text: str) -> None:
        self._append(LogEntry("mood", text))

    def _read_jsonl(self, path: Path) -> list:
        if not path.exists():
            return []
        out = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
        return out

    def read_today(self) -> list:
        return self._read_jsonl(self._jsonl_path())

    def read_date(self, d: str) -> list:
        return self._read_jsonl(self.root / f"{d}.jsonl")

    def search(self, tag: str | None = None, kind: str | None = None) -> list:
        out = []
        for p in self.root.glob("*.jsonl"):
            for e in self._read_jsonl(p):
                if kind and e.get("kind") != kind:
                    continue
                if tag and tag not in str(e.get("meta", {})):
                    continue
                out.append(e)
        return out

    def markdown_today(self) -> str:
        entries = self.read_today()
        if not entries:
            return f"# Logbook {self._today_str()}\n\n(пусто)"
        lines = [f"# Logbook {self._today_str()}", ""]
        by_kind = {}
        for e in entries:
            by_kind.setdefault(e["kind"], []).append(e)
        for kind in ("event", "decision", "unresolved", "mood"):
            items = by_kind.get(kind, [])
            if not items:
                continue
            lines.append(f"## {kind}")
            for e in items:
                ts = datetime.fromtimestamp(e["ts"]).strftime("%H:%M")
                lines.append(f"- {ts} — {e['text']}")
            lines.append("")
        return "\n".join(lines)

    def write_markdown_today(self) -> Path:
        p = self._md_path()
        p.write_text(self.markdown_today(), encoding="utf-8")
        return p


__all__ = ["DEFAULT_ROOT", "LogEntry", "Logbook"]
