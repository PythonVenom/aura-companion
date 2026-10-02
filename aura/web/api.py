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
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


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


def create_app(orchestrator=None, bridge=None) -> FastAPI:
    app = FastAPI(title="Aura API", version="0.1.0")
    _orch = orchestrator

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
        # MVP: пишем в inbox (watcher обработает) + синхронный ответ через orchestrator
        _append_chat(text)
        aura_text = ""
        if _orch is not None:
            try:
                import asyncio
                aura_text = asyncio.run(_orch.process(text))
            except Exception as e:
                aura_text = f"error: {e}"
        return ChatResponse(user=text, aura=aura_text, ts=time.time())

    return app


__all__ = ["create_app", "ChatRequest", "ChatResponse"]
