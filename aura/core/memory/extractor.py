"""Extractor — LLM извлекает SPO-факты и сущности из диалога (ADR-122, 125).

Наука:
- MIRIX (Wang, Y. et al., 2025). Multi-Agent Memory System.
- A-Mem (2025). Agentic Memory with entity relations.
- SocialMemBench (2026). Benchmarking Social Memory in LLM Agents.

Использует Ollama format=json для structured output.
Если LLM недоступен — тихо возвращает пустой результат (не падает).
"""
from __future__ import annotations
import json
import urllib.request
from typing import Optional

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b-instruct-q4_K_M"
TIMEOUT = 30

SEMANTIC_PROMPT = (
    "Извлеки из реплики пользователя семантические факты в формате SPO. "
    "Верни ТОЛЬКО JSON: {\"facts\":[{\"subject\":\"...\","
    "\"predicate\":\"...\",\"object\":\"...\",\"confidence\":0.0-1.0}]}. "
    "Только устойчивые факты (предпочтения, свойства, родство). "
    "Игнорируй разовые команды. Если фактов нет — верни {\"facts\":[]}."
)

SOCIAL_PROMPT = (
    "Извлеки из реплики сущности (люди, роли) и связи между ними. "
    "Верни ТОЛЬКО JSON: {\"entities\":[{\"name\":\"...\",\"type\":\"person|role|thing\"}],"
    "\"relations\":[{\"src\":\"...\",\"kind\":\"PREFERS|DISLIKES|FAMILY_OF|HAS_ROLE\","
    "\"dst\":\"...\",\"weight\":0.0-1.0}],"
    "\"events\":[{\"entity\":\"...\",\"kind\":\"birthday|meeting|...\",\"date\":\"YYYY-MM-DD\"}]}. "
    "Если ничего нет — верни пустые массивы."
)


def _ollama_json(system_prompt: str, user_text: str) -> Optional[dict]:
    try:
        data = json.dumps({
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1, "num_predict": 300},
        }).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = json.loads(r.read().decode("utf-8"))
        text = body.get("message", {}).get("content", "").strip()
        if not text:
            return None
        return json.loads(text)
    except Exception:
        return None


def extract_semantic(text: str) -> list[dict]:
    """Вернуть список SPO-фактов из текста. Пустой список при неудаче."""
    obj = _ollama_json(SEMANTIC_PROMPT, text)
    if not obj:
        return []
    facts = obj.get("facts", [])
    return [f for f in facts if isinstance(f, dict)
            and f.get("subject") and f.get("predicate") and f.get("object")]


def extract_social(text: str) -> dict:
    """Вернуть {entities:[], relations:[], events:[]}."""
    obj = _ollama_json(SOCIAL_PROMPT, text)
    if not obj:
        return {"entities": [], "relations": [], "events": []}
    return {
        "entities": obj.get("entities", []) or [],
        "relations": obj.get("relations", []) or [],
        "events": obj.get("events", []) or [],
    }


def apply_semantic(text: str) -> int:
    """Извлечь и записать в SemanticMemory. Возврат: сколько записано."""
    from aura.core.memory.semantic import get_semantic, Fact
    s = get_semantic()
    if not s.check_ready():
        return 0
    n = 0
    for f in extract_semantic(text):
        try:
            fact = Fact(subject=str(f["subject"]),
                        predicate=str(f["predicate"]),
                        object=str(f["object"]),
                        confidence=float(f.get("confidence", 0.7)),
                        evidence=text[:200])
            if s.add(fact):
                n += 1
        except Exception:
            continue
    return n


def apply_social(text: str) -> int:
    """Извлечь и записать в SocialMemory. Возврат: сколько рёбер записано."""
    from aura.core.memory.social import get_social
    s = get_social()
    if not s.check_ready():
        return 0
    data = extract_social(text)
    n = 0
    for ent in data["entities"]:
        try:
            s.upsert_entity(str(ent["name"]), str(ent.get("type", "person")))
        except Exception:
            continue
    for r in data["relations"]:
        try:
            if s.add_relation(str(r["src"]), str(r["kind"]),
                              str(r.get("dst") or "") or None,
                              float(r.get("weight", 0.7)),
                              evidence=text[:200]):
                n += 1
        except Exception:
            continue
    for ev in data["events"]:
        try:
            s.add_event(str(ev["entity"]), str(ev["kind"]),
                        str(ev.get("date", "")))
        except Exception:
            continue
    return n
