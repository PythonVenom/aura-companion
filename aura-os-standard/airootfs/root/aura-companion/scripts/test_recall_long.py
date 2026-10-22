"""Долговременный тест ContextRecall — запись факта + проверка через N дней.

Стратегия: каждый день пишем факт, каждую неделю проверяем что помнит.
Крон запускает раз в сутки. Отчёт в ~/.cache/aura/recall_long.json
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

REPORT = Path.home() / ".cache" / "aura" / "recall_long.json"
FACTS_FILE = Path.home() / ".cache" / "aura" / "recall_facts.jsonl"


def log_fact(text: str) -> None:
    """Записать факт в RAG + локальный журнал."""
    try:
        from aura.agents.rag_memory import AgentRAGMemory
        r = AgentRAGMemory()
        r.remember("долговременный_тест", text)
    except Exception as e:
        print(f"RAG error: {e}")
    FACTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with FACTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "text": text}, ensure_ascii=False) + "\n")


def check_recall(days_ago: int = 30) -> dict:
    """Проверить, помнит ли факты 30-дневной давности."""
    if not FACTS_FILE.exists():
        return {"checked": 0, "found": 0, "accuracy": 0.0}
    now = time.time()
    threshold = now - days_ago * 86400
    facts = []
    with FACTS_FILE.open(encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
                if d["ts"] < threshold:
                    facts.append(d)
            except Exception:
                pass
    found = 0
    try:
        from aura.agents.rag_memory import AgentRAGMemory
        r = AgentRAGMemory()
        for fact in facts[:10]:  # первые 10
            results = r.recall(fact["text"][:50])
            if results:
                found += 1
    except Exception:
        pass
    return {
        "checked": len(facts),
        "found": found,
        "accuracy": found / len(facts) if facts else 0.0,
    }


def main() -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    # Ежедневный факт
    log_fact(f"Тест долговременной памяти от {today}. Капитан в добром здравии, корабль на курсе.")

    # Отчёт
    report = {
        "last_run": today,
        "facts_total": sum(1 for _ in FACTS_FILE.open()) if FACTS_FILE.exists() else 0,
        "recall_30d": check_recall(30),
        "recall_7d": check_recall(7),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
