"""
Общий клиент для Firefox native messaging bridge (ADR-011).

Используется browser_tabs и messenger — чтобы не дублировать
протокол length-prefix.

Протокол:
    4 байта LE длины + JSON.
    Каждый вызов — новый UNIX socket.
"""

from __future__ import annotations

import json
import socket
import struct

SOCKET_PATH = "/tmp/aura_firefox.sock"
DEFAULT_TIMEOUT = 5.0


def _load_token() -> str:
    """Bridge token (ADR-113). Мягкий режим."""
    from pathlib import Path as _P
    p = _P.home() / ".config" / "aura" / "bridge_token"
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def send_command(cmd: dict, timeout: float = DEFAULT_TIMEOUT) -> dict | None:
    """
    Отправить команду в bridge. Получить ответ.

    Возвращает dict. При ошибках — {"error": "..."}.
    """
    # ADR-113: добавляем токен (мягкий режим)
    tok = _load_token()
    if tok:
        cmd = {**cmd, "_token": tok}

    try:
        payload = json.dumps(cmd, ensure_ascii=False).encode("utf-8")
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect(SOCKET_PATH)
            s.sendall(struct.pack("@I", len(payload)) + payload)
            header = _recv_exact(s, 4)
            if not header:
                return None
            length = struct.unpack("@I", header)[0]
            body = _recv_exact(s, length)
            if not body:
                return None
            return json.loads(body.decode("utf-8"))
    except FileNotFoundError:
        return {"error": "bridge_not_running"}
    except TimeoutError:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": str(e)}


def _recv_exact(s: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = s.recv(n - len(buf))
        if not chunk:
            return b""
        buf += chunk
    return buf


def error_text(result: dict | None) -> str:
    """Человекочитаемая ошибка."""
    if result is None:
        return "❌ Firefox bridge не ответил"
    err = result.get("error", "unknown")
    if err == "bridge_not_running":
        return "❌ Firefox bridge не запущен (extension не загружен?)"
    if err == "timeout":
        return "❌ Firefox не ответил вовремя"
    if err == "max tab not found":
        return "❌ Вкладка Макса не найдена. Открой web.max.ru"
    if err == "not found":
        return "❌ Не найдено"
    return f"❌ Ошибка bridge: {err}"


__all__ = ["DEFAULT_TIMEOUT", "SOCKET_PATH", "error_text", "send_command"]
