#!/usr/bin/env python3
"""Socket server для bridge (Aura ↔ Firefox native messaging).

Aura пишет в /tmp/aura_firefox.sock (UNIX socket),
bridge host в Firefox читает и отвечает.
"""
import json
import os
import socket
import struct

SOCK = "/tmp/aura_firefox.sock"

# Bug 121: защита от OOM
MAX_MSG_SIZE = 10 * 1024 * 1024  # 10 МБ


def main():
    if os.path.exists(SOCK):
        os.unlink(SOCK)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(SOCK)
    srv.listen(1)
    print(f"aura-bridge: listening on {SOCK}", flush=True)
    while True:
        conn, _ = srv.accept()
        with conn:
            try:
                header = conn.recv(4)
                if not header:
                    continue
                length = struct.unpack("@I", header)[0]
                # Bug 121: защита от OOM
                if length > MAX_MSG_SIZE or length == 0:
                    continue
                body = b""
                while len(body) < length:
                    chunk = conn.recv(length - len(body))
                    if not chunk:
                        break
                    body += chunk
                msg = json.loads(body.decode("utf-8"))
                # MVP: echo + log
                reply = {"ok": True, "echo": msg, "server": "aura-bridge"}
                payload = json.dumps(reply, ensure_ascii=False).encode("utf-8")
                conn.sendall(struct.pack("@I", len(payload)) + payload)
            except Exception as e:
                err = json.dumps({"ok": False, "error": str(e)}).encode("utf-8")
                try:
                    conn.sendall(struct.pack("@I", len(err)) + err)
                except Exception:
                    pass


if __name__ == "__main__":
    main()
