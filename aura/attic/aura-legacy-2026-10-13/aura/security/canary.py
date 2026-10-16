"""Canary tokens — файлы-приманки (ADR-115)."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

CANARY_DIR = Path.home() / ".aura" / "canary"
HITS_LOG = Path.home() / ".cache" / "aura" / "canary_hits.jsonl"

_FAKE_FILES = {
    "passwords.txt": "admin:admin123\nroot:toor\n",
    "vault_backup.db": b"\x00\x01FAKE\x00\x02",
    "api_keys.json": '{"openai": "sk-fake-123", "vk": "fake_vk_token"}\n',
}

def install() -> list[str]:
    """Создать файлы-приманки. Идемпотентно."""
    CANARY_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(CANARY_DIR, 0o700)
    created = []
    for name, content in _FAKE_FILES.items():
        p = CANARY_DIR / name
        if not p.exists():
            if isinstance(content, bytes):
                p.write_bytes(content)
            else:
                p.write_text(content, encoding="utf-8")
            created.append(name)
    return created

def record_hit(action: str, payload: dict, source: str = "") -> None:
    """Зафиксировать касание ловушки."""
    HITS_LOG.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "ts": time.time(),
        "action": action,
        "source": source,
        "payload_keys": list(payload.keys()) if isinstance(payload, dict) else [],
    }
    with HITS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def hits() -> list[dict]:
    if not HITS_LOG.exists(): return []
    return [json.loads(l) for l in HITS_LOG.read_text(encoding="utf-8").strip().splitlines()]
