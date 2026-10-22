"""Memory Consolidation — HOT → WARM (LLM-summary).

Наука:
- Atkinson-Shiffrin 1968 (Hierarchical Memory)
- Squire 1992 (Consolidation during sleep)
- Fowler 2005 (Event Sourcing — append-only)

HOT  = chat_history.jsonl (7 дней, полный текст)
WARM = chat_history_weekly.jsonl (3 месяца, daily summary)
"""
from __future__ import annotations

import json
import logging
import urllib.request
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

log = logging.getLogger("aura.memory.consolidate")

CACHE = Path.home() / ".cache" / "aura"
HOT = CACHE / "chat_history.jsonl"
WARM = CACHE / "chat_history_weekly.jsonl"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma2:2b-instruct-q3_K_M"
HOT_RETENTION_DAYS = 7

PROMPT = (
    "Ты — Aura. Сожми диалоги за день в 5-10 строк от третьего лица. "
    "Что обсуждали, что решили, что запомнить о капитане. "
    "Без воды, только факты. Русский язык.\n\n"
    "Диалоги:\n{dialogues}\n\nСводка:"
)


def _load_hot_grouped() -> dict[str, list[dict]]:
    """Читает HOT, группирует по date. Пропускает записи без date."""
    if not HOT.exists():
        return {}
    grouped: dict[str, list[dict]] = defaultdict(list)
    with HOT.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            day = entry.get("date")
            if day:
                grouped[day].append(entry)
    return dict(grouped)


def _llm_summarize(dialogues: list[dict]) -> str:
    """LLM-summary через Ollama. Возвращает '' при ошибке."""
    lines = []
    for e in dialogues[:60]:
        u = (e.get("user") or "").strip()[:200]
        a = (e.get("aura") or "").strip()[:200]
        if u or a:
            lines.append(f"U: {u}\nA: {a}")
    body = "\n\n".join(lines)
    if not body:
        return ""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": PROMPT.format(dialogues=body),
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 500},
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            OLLAMA_URL, data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            obj = json.loads(r.read().decode("utf-8"))
        return (obj.get("response") or "").strip()
    except Exception as e:
        log.warning("llm_summarize failed: %s", e)
        return ""


def _append_warm(day: str, summary: str, n: int) -> None:
    """Дописать WARM-строку (append-only)."""
    WARM.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "date": day,
        "n_entries": n,
        "summary": summary,
        "ts": datetime.now(UTC).timestamp(),
    }
    with WARM.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        f.flush()


def _warm_has_day(day: str) -> bool:
    """Уже консолидирован этот день?"""
    if not WARM.exists():
        return False
    with WARM.open(encoding="utf-8") as f:
        for line in f:
            try:
                if json.loads(line).get("date") == day:
                    return True
            except json.JSONDecodeError:
                continue
    return False


def consolidate_old(days: int = HOT_RETENTION_DAYS) -> dict:
    """Консолидировать HOT-дни старше N дней → WARM.

    Возвращает {"processed": [...], "skipped": [...], "errors": [...]}.
    """
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    grouped = _load_hot_grouped()
    result: dict = {"processed": [], "skipped": [], "errors": []}
    for day, entries in sorted(grouped.items()):
        if day > cutoff:
            result["skipped"].append(day)
            continue
        if _warm_has_day(day):
            result["skipped"].append(day)
            continue
        summary = _llm_summarize(entries)
        if not summary:
            result["errors"].append(day)
            continue
        _append_warm(day, summary, len(entries))
        result["processed"].append(day)
        log.info("consolidated %s (%d entries)", day, len(entries))
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    r = consolidate_old()
    print(f"Processed: {r['processed']}")
    print(f"Skipped:   {len(r['skipped'])} days")
    print(f"Errors:    {r['errors']}")
