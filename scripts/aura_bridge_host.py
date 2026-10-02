#!/usr/bin/env python3
"""Native messaging host + socket server. Синхронный request/response."""
import json
import os
import queue
import socket
import struct
import sys
import threading


SOCK = "/tmp/aura_firefox.sock"


def read_msg(stream):
    raw = stream.read(4)
    if len(raw) < 4:
        return None
    length = struct.unpack("<I", raw)[0]
    body = stream.read(length)
    return json.loads(body.decode("utf-8"))


def write_msg(stream, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    stream.write(struct.pack("<I", len(data)))
    stream.write(data)
    stream.flush()


def socket_server(in_q: queue.Queue):
    if os.path.exists(SOCK):
        os.unlink(SOCK)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(SOCK)
    srv.listen(1)
    print(f"[bridge] socket: {SOCK}", file=sys.stderr, flush=True)
    while True:
        conn, _ = srv.accept()
        # читаем команду от Aura
        try:
            header = conn.recv(4)
            if not header:
                conn.close()
                continue
            length = struct.unpack("<I", header)[0]
            body = b""
            while len(body) < length:
                chunk = conn.recv(length - len(body))
                if not chunk:
                    break
                body += chunk
            cmd = json.loads(body.decode("utf-8"))
            in_q.put((conn, cmd))
        except Exception as e:
            print(f"[bridge] recv: {e}", file=sys.stderr, flush=True)
            try:
                conn.close()
            except Exception:
                pass


def main():
    in_q: queue.Queue = queue.Queue()
    threading.Thread(target=socket_server, args=(in_q,), daemon=True).start()

    # Main loop: synchronously send/recv with Firefox
    while True:
        try:
            conn, cmd = in_q.get()
        except KeyboardInterrupt:
            break
        try:
            write_msg(sys.stdout.buffer, cmd)
            reply = read_msg(sys.stdin.buffer)
            if reply is None:
                reply = {"error": "firefox closed"}
        except Exception as e:
            reply = {"error": str(e)}
        try:
            payload = json.dumps(reply, ensure_ascii=False).encode("utf-8")
            conn.sendall(struct.pack("<I", len(payload)) + payload)
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
