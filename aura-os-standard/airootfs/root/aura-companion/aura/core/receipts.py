"""Receipts — верификация критичных действий (Cairn-style).

Наука: Cairn on-chain coordination, ERC-8004.
Локальный fallback: hash-chain (без блокчейна, но проверяемо).
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

CHAIN_FILE = Path.home() / ".cache" / "aura" / "receipts.jsonl"


@dataclass
class Receipt:
    action: str
    actor: str
    payload: dict
    ts: float = field(default_factory=time.time)
    prev_hash: str = ""
    hash: str = ""

    def compute_hash(self) -> str:
        data = json.dumps({
            "action": self.action,
            "actor": self.actor,
            "payload": self.payload,
            "ts": self.ts,
            "prev_hash": self.prev_hash,
        }, sort_keys=True, ensure_ascii=False).encode()
        return hashlib.sha256(data).hexdigest()[:16]


def _last_hash() -> str:
    if not CHAIN_FILE.exists():
        return "0" * 16
    try:
        last = None
        with CHAIN_FILE.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last = line
        if last:
            return json.loads(last).get("hash", "0" * 16)
    except Exception:
        pass
    return "0" * 16


def record(action: str, actor: str, payload: dict | None = None) -> Receipt:
    """Записать верифицируемое действие."""
    r = Receipt(
        action=action,
        actor=actor,
        payload=payload or {},
        prev_hash=_last_hash(),
    )
    r.hash = r.compute_hash()
    try:
        CHAIN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with CHAIN_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
    except Exception:
        pass
    return r


def verify() -> tuple[bool, int]:
    """Проверить целостность цепочки. Возврат: (ok, count)."""
    if not CHAIN_FILE.exists():
        return True, 0
    prev = "0" * 16
    count = 0
    try:
        with CHAIN_FILE.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                r = Receipt(
                    action=d["action"], actor=d["actor"],
                    payload=d["payload"], ts=d["ts"],
                    prev_hash=d["prev_hash"], hash=d["hash"],
                )
                if r.prev_hash != prev:
                    return False, count
                if r.compute_hash() != r.hash:
                    return False, count
                prev = r.hash
                count += 1
    except Exception:
        return False, count
    return True, count


def stats() -> dict:
    ok, n = verify()
    return {"chain_ok": ok, "receipts": n, "file": str(CHAIN_FILE)}


__all__ = ["Receipt", "record", "stats", "verify"]
