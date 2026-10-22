"""Базовый MCP-клиент (JSON-RPC 2.0 over stdio)."""
from __future__ import annotations
import asyncio, json, logging
from typing import Any

log = logging.getLogger("aura.mcp.client")

class StdioMCPClient:
    def __init__(self, command: list[str], env: dict[str, str] | None = None):
        self.command = command
        self.env = env
        self.proc: asyncio.subprocess.Process | None = None
        self._req_id = 0
        self._pending: dict[int, asyncio.Future] = {}
        self._read_task: asyncio.Task | None = None

    async def start(self) -> None:
        import os
        env = os.environ.copy()
        if self.env:
            env.update(self.env)
        self.proc = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        self._read_task = asyncio.create_task(self._read_loop())
        
        await self.request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "aura-os", "version": "1.0"}
        })

    async def _read_loop(self) -> None:
        while self.proc and self.proc.stdout:
            line = await self.proc.stdout.readline()
            if not line:
                # Процесс умер. Резолвим все ожидающие фьючерсы с ошибкой
                for fut in self._pending.values():
                    if not fut.done():
                        fut.set_exception(RuntimeError("MCP process exited unexpectedly"))
                self._pending.clear()
                break
            try:
                msg = json.loads(line.decode("utf-8"))
                if "id" in msg and msg["id"] in self._pending:
                    fut = self._pending.pop(msg["id"])
                    if "error" in msg:
                        fut.set_exception(RuntimeError(msg["error"]))
                    else:
                        fut.set_result(msg.get("result"))
            except Exception as e:
                log.warning("MCP parse error: %s", e)

    async def request(self, method: str, params: dict | None = None) -> Any:
        if not self.proc or not self.proc.stdin:
            raise RuntimeError("MCP not started")
        self._req_id += 1
        req_id = self._req_id
        req = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params:
            req["params"] = params
        
        fut = asyncio.get_running_loop().create_future()
        self._pending[req_id] = fut
        
        self.proc.stdin.write((json.dumps(req) + "\n").encode("utf-8"))
        await self.proc.stdin.drain()
        
        return await asyncio.wait_for(fut, timeout=30.0)

    async def list_tools(self) -> list[dict]:
        res = await self.request("tools/list")
        return res.get("tools", [])

    async def call_tool(self, name: str, arguments: dict) -> Any:
        return await self.request("tools/call", {"name": name, "arguments": arguments})

    async def stop(self) -> None:
        if self._read_task:
            self._read_task.cancel()
        if self.proc:
            self.proc.terminate()
            await self.proc.wait()


# Обратная совместимость для kernel.agents.mcp_agent
MCPClient = StdioMCPClient
