"""HTTP API Aura — DE-agnostic слой (ADR-079).

Endpoints:
  GET  /health         — health check (без auth)
  GET  /status         — состояние Aura (state, version, uptime)
  GET  /version        — версия Aura
  GET  /agents         — список агентов
  GET  /chat/history   — история чата (JSONL)
  POST /chat           — отправить сообщение в чат

Работает на localhost:8765. Без auth (для LAN/dev).
Production: TLS + token — позже (ADR-079 v2).
"""
from __future__ import annotations
import json
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# DEDUP (Bug 74): защита от API-loop
_LAST_CHAT: dict = {}  # {user_text: ts}
_DEDUP_SEC = 2.0


class ChatRequest(BaseModel):
    user: str


class ChatResponse(BaseModel):
    user: str
    aura: str
    ts: float


def _read_status() -> dict:
    p = Path.home() / ".cache/aura/aura_status.json"
    if not p.exists():
        return {"state": "unknown", "text": ""}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"state": "error", "text": "parse error"}


def _read_chat_history(limit: int = 100) -> list:
    p = Path.home() / ".cache/aura/chat_history.jsonl"
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def _append_chat(user: str) -> None:
    p = Path.home() / ".cache/aura/chat_inbox.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps({"user": user, "ts": time.time()}, ensure_ascii=False) + "\n")




def _read_ui_html() -> str:
    from pathlib import Path as _P
    p = _P(__file__).parent / "ui.html"
    if p.exists():
        return p.read_text(encoding="utf-8")
    return "<html><body><h1>Aura UI not found</h1></body></html>"


def create_app(orchestrator=None, bridge=None) -> FastAPI:
    app = FastAPI(title="Aura API", version="0.1.0")
    _orch = orchestrator


    @app.get("/ui", response_class=None)
    def ui():
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=_read_ui_html())
    @app.get("/health")
    def health():
        return {"status": "ok", "ts": time.time()}

    @app.get("/version")
    def version():
        try:
            from aura import __version__
            return {"version": __version__}
        except Exception:
            return {"version": "unknown"}

    @app.get("/status")
    def status():
        st = _read_status()
        st["version"] = version()["version"]
        return st

    @app.get("/agents")
    def agents():
        names = []
        if _orch is not None and hasattr(_orch, "registry"):
            try:
                names = _orch.registry.list_names()
            except Exception:
                pass
        return {"agents": names, "count": len(names)}

    @app.get("/chat/history")
    def chat_history(limit: int = 100):
        return _read_chat_history(limit=limit)

    @app.post("/chat", response_model=ChatResponse)
    def chat(req: ChatRequest):
        text = (req.user or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="empty user message")
        # DEDUP (Bug 74): не принимать тот же текст < 2 сек
        import time as _t
        now = _t.time()
        last = _LAST_CHAT.get(text, 0)
        if now - last < _DEDUP_SEC:
            print(f"🔇 API dedup: {text[:40]}")
            return ChatResponse(user=text, aura="(dedup)", ts=now)
        _LAST_CHAT[text] = now
        # Чистка старых ключей
        if len(_LAST_CHAT) > 100:
            cutoff = now - 60
            _LAST_CHAT.clear()
            _LAST_CHAT.update({k: v for k, v in _LAST_CHAT.items() if v > cutoff})
        # MVP: пишем в inbox (watcher обработает) + синхронный ответ через orchestrator
        # File-based IPC: пишем в inbox, watcher обработает,
        # UI поллит /chat/history через 2-3 сек.
        # Sync-ответ не нужен (см. ADR-069, ADR-079).
        _append_chat(text)
        return ChatResponse(user=text, aura="", ts=time.time())

    return app


__all__ = ["create_app", "ChatRequest", "ChatResponse"]
