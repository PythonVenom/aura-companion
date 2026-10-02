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
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

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

    def _embed(self, text: str) -> Optional[list[float]]:
        try:
            data = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode("utf-8")
            req = urllib.request.Request(EMBED_URL, data=data,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode("utf-8")).get("embedding")
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
