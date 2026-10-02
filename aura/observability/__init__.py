"""Structured logging + trace (ADR-112). Без внешних зависимостей."""
from __future__ import annotations
import json, time, uuid, os
from pathlib import Path
from datetime import datetime, timezone

_LOG_PATH = Path(os.path.expanduser("~/.cache/aura/logs.jsonl"))
_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

_current: dict = {"trace_id": None, "span_id": None}

def new_trace(name: str = "root") -> str:
    tid = uuid.uuid4().hex[:12]
    _current["trace_id"] = tid
    log("trace.start", name=name)
    return tid

def new_span(name: str) -> str:
    sid = uuid.uuid4().hex[:8]
    _current["span_id"] = sid
    log("span.start", name=name)
    return sid

def log(event: str, **fields) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "trace_id": _current.get("trace_id"),
        "span_id": _current.get("span_id"),
    }
    rec.update(fields)
    try:
        with _LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass

def tail(n: int = 20) -> list[dict]:
    if not _LOG_PATH.exists(): return []
    lines = _LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(x) for x in lines[-n:]]
