"""MCP (Model Context Protocol) adapter — совместимость с внешними инструментами.

Наука: Anthropic MCP (2024) — аналог USB для AI-инструментов.
Позволяет AURA вызывать внешние MCP-серверы как агентов.

Формат: JSON-RPC 2.0 по stdio.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MCPServer:
    name: str
    command: list[str]
    tools: list[dict] = field(default_factory=list)
    _proc: object = None

    def start(self) -> bool:
        try:
            self._proc = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self._call("initialize", {"protocolVersion": "2024-11-05"})
            resp = self._call("tools/list", {})
            self.tools = resp.get("tools", [])
            return True
        except Exception:
            return False

    def _call(self, method: str, params: dict) -> dict:
        proc = self._proc
        if proc is None or proc.stdin is None:
            return {}
        req = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        proc.stdin.write((json.dumps(req) + chr(10)).encode())
        proc.stdin.flush()
        line = proc.stdout.readline().decode() if proc.stdout else ""
        try:
            return json.loads(line).get("result", {})
        except Exception:
            return {}

    def call_tool(self, tool_name: str, args: dict) -> dict:
        return self._call("tools/call", {"name": tool_name, "arguments": args})

    def stop(self) -> None:
        if self._proc is not None:
            self._proc.terminate()


CONFIG_PATH = Path.home() / ".config" / "aura" / "mcp_servers.json"


def load_servers() -> list[MCPServer]:
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return [
                MCPServer(name=s["name"], command=s["command"])
                for s in data.get("servers", [])
            ]
    except Exception:
        pass
    return []


__all__ = ["MCPServer", "load_servers", "CONFIG_PATH"]
