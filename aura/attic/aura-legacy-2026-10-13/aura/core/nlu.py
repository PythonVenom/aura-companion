"""NLU — embeddings intent (ADR-132).

Наука:
- Reimers, N. & Gurevych, I. (2019). Sentence-BERT. EMNLP.
- Devlin, J. et al. (2019). BERT. NAACL.

Гибрид: regex (RouteTree) → embedding если regex не сработал.
Embedding: nomic-embed-text via Ollama.
"""
from __future__ import annotations

import json
import math
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/embeddings"
MODEL = "nomic-embed-text"
THRESHOLD = 0.55

EXAMPLES = {
    "music": [
        "включи музыку", "поставь песню", "играй трек", "хочу послушать",
        "следующая песня", "предыдущий трек", "пауза музыки",
    ],
    "time": [
        "который час", "сколько времени", "какое сегодня число", "дата",
        "какой день недели",
    ],
    "power": [
        "заблокируй экран", "залочь", "lock screen",
    ],
    "app": [
        "открой firefox", "запусти терминал", "открой vscode",
        "запусти приложение",
    ],
    "browser": [
        "открой сайт", "открой ссылку", "открой в браузере", "открой https",
    ],
    "control": [
        "пауза", "продолжи", "замолчи", "стоп", "перезапусти",
    ],
    "care": [
        "напомни", "напоминание", "поставь будильник",
    ],
}

_EMB_CACHE: dict = {}
_CENTROIDS: dict | None = None


def _embed(text: str) -> list | None:
    if text in _EMB_CACHE:
        return _EMB_CACHE[text]
    try:
        data = json.dumps({"model": MODEL, "prompt": text}).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            emb = json.loads(r.read().decode("utf-8")).get("embedding")
        if emb:
            _EMB_CACHE[text] = emb
        return emb
    except Exception:
        return None


def _cosine(a: list, b: list) -> float:
    if not a or not b:
        return 0.0
    num = sum(x * y for x, y in zip(a, b, strict=False))
    da = math.sqrt(sum(x * x for x in a))
    db = math.sqrt(sum(y * y for y in b))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


def _route_centroids() -> dict:
    out = {}
    for route, exs in EXAMPLES.items():
        embs = [e for e in (_embed(x) for x in exs) if e]
        if not embs:
            continue
        dim = len(embs[0])
        avg = [sum(e[i] for e in embs) / len(embs) for i in range(dim)]
        out[route] = avg
    return out


def classify(text: str) -> tuple:
    """(route_or_None, confidence)."""
    global _CENTROIDS
    if _CENTROIDS is None:
        _CENTROIDS = _route_centroids()
    if not _CENTROIDS:
        return None, 0.0
    emb = _embed(text)
    if not emb:
        return None, 0.0
    best_route, best_sim = None, 0.0
    for route, cent in _CENTROIDS.items():
        sim = _cosine(emb, cent)
        if sim > best_sim:
            best_route, best_sim = route, sim
    if best_sim < THRESHOLD:
        return None, round(best_sim, 3)
    return best_route, round(best_sim, 3)


def available() -> bool:
    """Проверка, что Ollama embeddings отвечает."""
    return _embed("ping") is not None
