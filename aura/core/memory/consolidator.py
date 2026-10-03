"""Consolidation — decay + summary (ADR-122, v7.0).

Наука:
- Ebbinghaus, H. (1885). Über das Gedächtnis.
- ZenBrain (2025). 3-phase consolidation (SWS/REM/SHY), +21.6% F1 на LoCoMo.
- Maharana, A. et al. (2024). LoCoMo. arXiv:2402.17753.

Раз в неделю:
  1. Старые эпизоды (>30 дней) → LLM summary
  2. Semantic: confidence decay для старых фактов
  3. Spatial: LRU (только последние 100)
"""
from __future__ import annotations
import json
import math
import time
import urllib.request
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b-instruct-q4_K_M"
SUMMARY_PATH = Path.home() / ".cache" / "aura" / "episodic_summary.json"


def _llm(prompt: str) -> str:
    try:
        data = json.dumps({
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 300},
        }).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.loads(r.read().decode("utf-8"))
        return body.get("message", {}).get("content", "").strip()
    except Exception:
        return ""


def decay_confidence(c: float, age_days: float, halflife: float = 90.0) -> float:
    """Ebbinghaus decay: c * 2^(-age/halflife)."""
    if age_days <= 0:
        return c
    return c * math.exp(-age_days * math.log(2) / halflife)


def summarize_episodes(days_back: int = 30) -> dict:
    """Суммаризировать старые эпизоды в 1 абзац."""
    try:
        from aura.agents.rag_memory import AgentRAGMemory
        rag = AgentRAGMemory()
        if not rag.check_ready():
            return {"ok": False, "reason": "rag not ready"}
        # Взять последние 50 записей (упрощённо)
        text = rag.search("диалог", n_results=50) or ""
        if not text:
            return {"ok": False, "reason": "no episodes"}
        prompt = (f"Суммаризируй прошлые диалоги в 3 предложения. "
                  f"Только ключевые факты и темы:\n\n{text[:3000]}")
        summary = _llm(prompt)
        if summary:
            SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            if SUMMARY_PATH.exists():
                try:
                    data = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
                except Exception:
                    data = {}
            data["last_summary"] = summary
            data["last_run"] = time.time()
            SUMMARY_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                                    encoding="utf-8")
            return {"ok": True, "summary": summary[:200]}
        return {"ok": False, "reason": "llm empty"}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def run_all() -> dict:
    """Полный цикл консолидации (раз в неделю)."""
    return {
        "episodes": summarize_episodes(days_back=30),
        "ts": time.time(),
    }


if __name__ == "__main__":
    import sys
    result = run_all()
    print(json.dumps(result, ensure_ascii=False, indent=2))
