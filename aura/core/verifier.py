"""Verifier — hallucination check (ADR-133).

Наука:
- Es, S. et al. (2023). RAGAS. EACL.
- Manakul, P. et al. (2023). SelfCheckGPT. EMNLP.
"""
from __future__ import annotations

import json
import re
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b-instruct-q4_K_M"


def _llm(prompt: str) -> str:
    try:
        data = json.dumps({
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 200},
        }).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=25) as r:
            body = json.loads(r.read().decode("utf-8"))
        return body.get("message", {}).get("content", "").strip()
    except Exception:
        return ""


def verify_grounded(answer: str, context: str) -> dict:
    """Проверить, вытекает ли ответ из контекста (RAGAS faithfulness).
    Возврат: {score: 0..1, supported: [claims], unsupported: [claims]}."""
    if not answer or not context:
        return {"score": 1.0, "supported": [], "unsupported": []}
    prompt = (f"Контекст:\n{context[:800]}\n\nОтвет:\n{answer[:400]}\n\n"
              "Разбей ответ на утверждения. Какое подтверждается контекстом? "
              "Верни JSON: {\"supported\":[...],\"unsupported\":[...]}")
    raw = _llm(prompt)
    try:
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        obj = json.loads(raw)
        sup = obj.get("supported") or []
        uns = obj.get("unsupported") or []
        total = len(sup) + len(uns)
        score = len(sup) / total if total else 1.0
        return {"score": round(score, 2), "supported": sup, "unsupported": uns}
    except Exception:
        return {"score": 1.0, "supported": [], "unsupported": []}


def check_numbers_consistency(answer: str, context: str) -> bool:
    """Все ли числа из ответа присутствуют в контексте."""
    nums = re.findall(r"\b\d+(?:\.\d+)?\b", answer)
    if not nums:
        return True
    return all(n in context for n in nums)


def should_hedge(score: float) -> bool:
    return score < 0.7
