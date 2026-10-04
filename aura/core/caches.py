"""Caches — LRU для embeddings/prompts (ADR-153).

Наука:
- Gim, I., Chen, G., et al. (2023). Prompt Cache: Modular Attention Reuse.
  arXiv:2311.04934. (MLSys 2024)
"""
from __future__ import annotations
import hashlib
from collections import OrderedDict
from typing import Any, Optional


class LRUCache:
    def __init__(self, maxsize: int = 200) -> None:
        self.maxsize = maxsize
        self._d: OrderedDict = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if key in self._d:
            self._d.move_to_end(key)
            return self._d[key]
        return None

    def put(self, key: str, val: Any) -> None:
        self._d[key] = val
        self._d.move_to_end(key)
        while len(self._d) > self.maxsize:
            self._d.popitem(last=False)

    def __len__(self) -> int:
        return len(self._d)


_EMB = LRUCache(500)
_PROMPT = LRUCache(50)
_TEMPLATE = LRUCache(100)


def emb_key(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def emb_get(text: str):
    return _EMB.get(emb_key(text))


def emb_put(text: str, emb: list) -> None:
    _EMB.put(emb_key(text), emb)


def prompt_get(system: str, user: str):
    return _PROMPT.get(hashlib.md5(f"{system}||{user}".encode()).hexdigest())


def prompt_put(system: str, user: str, response: str) -> None:
    _PROMPT.put(hashlib.md5(f"{system}||{user}".encode()).hexdigest(), response)


def stats() -> dict:
    return {"embeddings": len(_EMB), "prompts": len(_PROMPT), "templates": len(_TEMPLATE)}
