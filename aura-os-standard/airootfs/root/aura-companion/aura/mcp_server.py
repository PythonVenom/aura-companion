"""MCP-сервер для Aura — stdio JSON-RPC.

Протокол: MCP 2024-11-05.
Транспорт: stdio (line-delimited JSON).
Без зависимостей — чистый stdlib.

Инструменты:
  - aura_chat:   отправить сообщение Aura, дождаться ответа
  - aura_status: статус сервиса
  - aura_agents: список агентов
  - aura_doctor: диагностика

Использование (Claude Desktop config):
  "command": "/path/to/venv/bin/python",
  "args": ["-m", "aura.cli", "serve", "--mcp"]
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

CACHE = Path(os.environ.get(
    "AURA_CACHE_DIR", str(Path.home() / ".cache/aura")
))
INBOX = CACHE / "chat_inbox.jsonl"
HISTORY = CACHE / "chat_history.jsonl"

SERVER_INFO = {"name": "aura-mcp", "version": "0.1.0"}
PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "aura_chat",
        "description": "Отправить сообщение локальному ИИ-компаньону Aura и получить ответ",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Текст сообщения"},
                "timeout": {
                    "type": "number",
                    "description": "Таймаут в секундах",
                    "default": 30,
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "aura_status",
        "description": "Проверить статус сервиса Aura",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "aura_agents",
        "description": "Список доступных агентов Aura",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "aura_doctor",
        "description": "Запустить диагностику Aura",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def _send(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _reply(id_, result=None, error=None) -> None:
    obj = {"jsonrpc": "2.0", "id": id_}
    if error is not None:
        obj["error"] = error
    else:
        obj["result"] = result
    _send(obj)


def _cli(*args: str, timeout: float = 15.0) -> str:
    try:
        r = subprocess.run(
            [sys.executable, "-m", "aura.cli", *args],
            capture_output=True, text=True, timeout=timeout,
        )
        return (r.stdout + r.stderr).strip() or "(пусто)"
    except subprocess.TimeoutExpired:
        return f"⏱ Таймаут ({timeout}с)"
    except Exception as e:
        return f"❌ {e}"


def tool_chat(text: str, timeout: float = 30.0) -> str:
    if not text.strip():
        return "❌ Пустое сообщение"
    INBOX.parent.mkdir(parents=True, exist_ok=True)
    offset = HISTORY.stat().st_size if HISTORY.exists() else 0
    ts = time.time()
    with open(INBOX, "a", encoding="utf-8") as f:
        f.write(json.dumps({"user": text, "ts": ts}, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())

    deadline = time.time() + timeout
    while time.time() < deadline:
        if HISTORY.exists() and HISTORY.stat().st_size > offset:
            with open(HISTORY, encoding="utf-8") as f:
                f.seek(offset)
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except Exception:
                        continue
                    if entry.get("user") == text:
                        return entry.get("aura", "(пустой ответ)")
        time.sleep(0.3)
    return f"⏱ Aura не ответила за {int(timeout)}с"


def tool_status() -> str:
    return _cli("status")


def tool_agents() -> str:
    return _cli("agents")


def tool_doctor() -> str:
    return _cli("doctor")


def _handle(msg: dict):
    method = msg.get("method")
    msg.get("id")
    params = msg.get("params", {})

    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        }
    if method == "initialized":
        return None
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {}) or {}
        if name == "aura_chat":
            text = args.get("text", "")
            timeout = float(args.get("timeout", 30))
            out = tool_chat(text, timeout)
        elif name == "aura_status":
            out = tool_status()
        elif name == "aura_agents":
            out = tool_agents()
        elif name == "aura_doctor":
            out = tool_doctor()
        else:
            return {"content": [{"type": "text", "text": f"❌ Неизвестный инструмент: {name}"}],
                    "isError": True}
        return {"content": [{"type": "text", "text": out}]}
    raise ValueError(f"Unknown method: {method}")


def main() -> None:
    """Главный цикл MCP-сервера: читаем stdin, пишем stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        id_ = msg.get("id")
        method = msg.get("method")
        if method is None:
            continue
        try:
            result = _handle(msg)
            if id_ is not None and result is not None:
                _reply(id_, result=result)
        except Exception as e:
            if id_ is not None:
                _reply(id_, error={"code": -32603, "message": str(e)})


if __name__ == "__main__":
    main()
