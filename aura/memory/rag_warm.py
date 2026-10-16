"""RAG по WARM (chat_history_weekly.jsonl) — семантический поиск по дням.

Наука:
- GraphRAG / Vector RAG (Lewis 2020)
- Отдельная коллекция от HOT: чтобы recall week != recall dialog
"""
from __future__ import annotations

import json
import logging
import urllib.request
from pathlib import Path

log = logging.getLogger("aura.memory.rag_warm")

CACHE = Path.home() / ".cache" / "aura"
WARM = CACHE / "chat_history_weekly.jsonl"
CHROMA_DIR = CACHE / "chroma"
COLLECTION = "chat_weekly"
EMBED_URL = "http://localhost:11434/api/embed"
EMBED_MODEL = "nomic-embed-text"


def _embed(text: str) -> list[float] | None:
    payload = {"model": EMBED_MODEL, "input": text}
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            EMBED_URL, data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            obj = json.loads(r.read().decode("utf-8"))
        embs = obj.get("embeddings") or []
        return embs[0] if embs else None
    except Exception as e:
        log.warning("embed failed: %s", e)
        return None


def _client():
    try:
        import chromadb
        return chromadb.PersistentClient(path=str(CHROMA_DIR))
    except Exception as e:
        log.warning("chroma init failed: %s", e)
        return None


def index_warm() -> dict:
    """Проиндексировать WARM в ChromaDB (idempotent — по id=date)."""
    if not WARM.exists():
        return {"indexed": 0, "skipped": 0, "errors": ["no WARM file"]}
    client = _client()
    if client is None:
        return {"indexed": 0, "skipped": 0, "errors": ["chroma not available"]}
    coll = client.get_or_create_collection(COLLECTION)
    indexed, skipped, errors = 0, 0, []
    existing = set(coll.get().get("ids") or [])
    with WARM.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            day = obj.get("date")
            summary = obj.get("summary") or ""
            if not day or not summary:
                skipped += 1
                continue
            if day in existing:
                skipped += 1
                continue
            emb = _embed(summary)
            if not emb:
                errors.append(day)
                continue
            try:
                coll.add(
                    ids=[day],
                    documents=[summary],
                    embeddings=[emb],
                    metadatas=[{"date": day, "n": obj.get("n_entries", 0)}],
                )
                indexed += 1
            except Exception as e:
                errors.append(f"{day}: {e}")
    return {"indexed": indexed, "skipped": skipped, "errors": errors}


def recall_week(query: str, n: int = 3) -> list[dict]:
    """Найти N дней, семантически близких к query."""
    client = _client()
    if client is None:
        return []
    coll = client.get_or_create_collection(COLLECTION)
    if coll.count() == 0:
        return []
    emb = _embed(query)
    if not emb:
        return []
    try:
        res = coll.query(query_embeddings=[emb], n_results=min(n, coll.count()))
    except Exception as e:
        log.warning("query failed: %s", e)
        return []
    out = []
    ids = res.get("ids", [[]])[0]
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    for i, day in enumerate(ids):
        out.append({
            "date": day,
            "summary": docs[i] if i < len(docs) else "",
            "n": metas[i].get("n", 0) if i < len(metas) else 0,
            "distance": dists[i] if i < len(dists) else None,
        })
    return out


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) > 1 and sys.argv[1] == "index":
        r = index_warm()
        print(f"Indexed: {r['indexed']}, Skipped: {r['skipped']}, Errors: {r['errors']}")
    elif len(sys.argv) > 1 and sys.argv[1] == "recall":
        q = " ".join(sys.argv[2:]) or "что обсуждали"
        for r in recall_week(q, n=3):
            print(f"[{r['date']}] n={r['n']} dist={r['distance']:.3f}")
            print(r["summary"][:200])
            print("---")
