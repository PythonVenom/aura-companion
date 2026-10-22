"""Semantic Memory — факты SPO + confidence (ADR-122, слой 4).

Наука:
- Tulving, E. (1972). Episodic and Semantic Memory.
- MIRIX (Wang, Y. et al., 2025). Multi-Agent Memory System — semantic layer.
- Kadavath, S. et al. (2022). Language Models (Mostly) Know What They Know.
  Anthropic — confidence signal.

Формат факта: (subject, predicate, object, confidence, evidence, ts).
Хранение: ChromaDB коллекция 'facts' (общая с episodic по дизайну).
Embedding: Ollama (nomic-embed-text или mxbai-embed-large).
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

DB_PATH = Path(os.path.expanduser("~/.cache/aura/chroma"))
COLLECTION = "semantic_facts"
EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"


@dataclass
class Fact:
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    evidence: str = ""
    ts: float = 0.0

    def to_text(self) -> str:
        return f"{self.subject} {self.predicate} {self.object}"


class SemanticMemory:
    def __init__(self) -> None:
        self._client = None
        self._coll = None
        self._ready = False
        self._init()

    def _init(self) -> None:
        try:
            import chromadb
            DB_PATH.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(DB_PATH))
            self._coll = self._client.get_or_create_collection(COLLECTION)
            self._ready = True
        except Exception as e:
            print(f"⚠️ Semantic memory init: {e}")

    def check_ready(self) -> bool:
        return self._ready

    def _embed(self, text: str) -> list[float] | None:
        # CACHE_V7 (ADR-153): LRU
        try:
            from aura.core.caches import emb_get, emb_put
            cached = emb_get(text)
            if cached:
                return cached
        except Exception:
            emb_put = lambda *a, **kw: None
        try:
            data = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode("utf-8")
            req = urllib.request.Request(EMBED_URL, data=data,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                emb = json.loads(r.read().decode("utf-8")).get("embedding")
                if emb:
                    try:
                        emb_put(text, emb)
                    except Exception as e:
                        # F-006: не глотать (раздел 17 промта)
                        import logging
                        logging.getLogger('aura.semantic').warning(
                            'semantic error: %s', e)
                return emb
        except Exception:
            return None

    def add(self, fact: Fact) -> bool:
        if not self._ready:
            return False
        emb = self._embed(fact.to_text())
        if emb is None:
            return False
        if fact.ts == 0.0:
            fact.ts = time.time()
        fid = f"{fact.subject}:{fact.predicate}:{fact.object}:{int(fact.ts)}"
        try:
            self._coll.add(
                ids=[fid],
                embeddings=[emb],
                documents=[fact.to_text()],
                metadatas=[asdict(fact)],
            )
            return True
        except Exception as e:
            print(f"⚠️ semantic.add: {e}")
            return False

    def search(self, query: str, n: int = 5) -> list[Fact]:
        if not self._ready:
            return []
        emb = self._embed(query)
        if emb is None:
            return []
        try:
            r = self._coll.query(query_embeddings=[emb], n_results=n)
        except Exception:
            return []
        out: list[Fact] = []
        for meta in (r.get("metadatas") or [[]])[0]:
            try:
                out.append(Fact(**{k: meta[k] for k in
                                   ("subject","predicate","object","confidence",
                                    "evidence","ts") if k in meta}))
            except Exception:
                continue
        return out

    def by_subject(self, subject: str, n: int = 20) -> list[Fact]:
        if not self._ready:
            return []
        try:
            r = self._coll.get(where={"subject": subject}, limit=n)
        except Exception:
            return []
        out: list[Fact] = []
        for meta in (r.get("metadatas") or []):
            try:
                out.append(Fact(**{k: meta[k] for k in
                                   ("subject","predicate","object","confidence",
                                    "evidence","ts") if k in meta}))
            except Exception:
                continue
        return out

    def forget(self, fact_id: str) -> bool:
        """Удалить факт по id (id = sha факта)."""
        if not self._ready or self._coll is None:
            return False
        try:
            self._coll.delete(ids=[fact_id])
            return True
        except Exception:
            return False

    def decay(self, max_age_days: int = 90, min_confidence: float = 0.3) -> int:
        """Забыть старые/неуверенные факты (Ebbinghaus 1885).

        Удаляет факты старше max_age_days ИЛИ confidence < min_confidence.
        Возвращает число удалённых.
        """
        if not self._ready or self._coll is None:
            return 0
        import time as _t
        now = _t.time()
        threshold = now - max_age_days * 86400
        try:
            data = self._coll.get(include=["metadatas"])
            ids = data.get("ids", [])
            metas = data.get("metadatas", [])
            to_delete = []
            for i, meta in zip(ids, metas, strict=False):
                ts = meta.get("ts", 0)
                conf = meta.get("confidence", 1.0)
                if (ts and ts < threshold) or conf < min_confidence:
                    to_delete.append(i)
            if to_delete:
                self._coll.delete(ids=to_delete)
            return len(to_delete)
        except Exception:
            return 0

    def consolidate(self) -> int:
        """Слить дубли: одинаковые subject+predicate+object → 1 факт.

        Возвращает число удалённых дублей.
        """
        if not self._ready or self._coll is None:
            return 0
        try:
            data = self._coll.get(include=["metadatas", "documents"])
            ids = data.get("ids", [])
            docs = data.get("documents", [])
            seen: dict[str, str] = {}
            to_delete = []
            for i, doc in zip(ids, docs, strict=False):
                key = doc.strip().lower()
                if key in seen:
                    to_delete.append(i)
                else:
                    seen[key] = i
            if to_delete:
                self._coll.delete(ids=to_delete)
            return len(to_delete)
        except Exception:
            return 0

    def contradictions(self, subject: str) -> list[dict]:
        """Найти противоречия: разные object при одинаковом subject+predicate."""
        if not self._ready or self._coll is None:
            return []
        try:
            data = self._coll.get(include=["metadatas", "documents"])
            docs = data.get("documents", [])
            metas = data.get("metadatas", [])
            groups: dict[str, list[dict]] = {}
            for doc, meta in zip(docs, metas, strict=False):
                if meta.get("subject", "").lower() != subject.lower():
                    continue
                key = meta.get("predicate", "")
                groups.setdefault(key, []).append({
                    "object": meta.get("object", ""),
                    "doc": doc,
                })
            return [
                {"predicate": pred, "variants": variants}
                for pred, variants in groups.items()
                if len({v["object"] for v in variants}) > 1
            ]
        except Exception:
            return []

    def by_object(self, obj: str, n: int = 20) -> list[Fact]:
        """Найти факты по object."""
        if not self._ready or self._coll is None:
            return []
        try:
            data = self._coll.get(include=["metadatas"])
            metas = data.get("metadatas", [])
            results = []
            for meta in metas:
                if obj.lower() in meta.get("object", "").lower():
                    results.append(Fact(
                        subject=meta.get("subject", ""),
                        predicate=meta.get("predicate", ""),
                        object=meta.get("object", ""),
                        confidence=meta.get("confidence", 1.0),
                        ts=meta.get("ts", 0.0),
                    ))
            return results[:n]
        except Exception:
            return []

    def stats(self) -> dict:
        if not self._ready:
            return {"ready": False}
        try:
            return {"ready": True, "count": self._coll.count()}
        except Exception:
            return {"ready": True, "count": -1}


_SINGLETON: SemanticMemory | None = None


def get_semantic() -> SemanticMemory:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = SemanticMemory()
    return _SINGLETON
