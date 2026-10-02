#!/usr/bin/env python3
"""Native messaging host для Firefox (Aura Bridge).

Firefox → stdin → host → socket /tmp/aura_firefox.sock → server
Server → socket → host → stdout → Firefox
"""
import json
import socket
import struct
import sys


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


def main():
    while True:
        try:
            msg = read_msg(sys.stdin.buffer)
            if msg is None:
                break
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect(SOCK)
                payload = json.dumps(msg, ensure_ascii=False).encode("utf-8")
                s.sendall(struct.pack("<I", len(payload)) + payload)
                hdr = s.recv(4)
                if not hdr:
                    write_msg(sys.stdout.buffer, {"error": "no response"})
                    continue
                n = struct.unpack("<I", hdr)[0]
                body = b""
                while len(body) < n:
                    chunk = s.recv(n - len(body))
                    if not chunk:
                        break
                    body += chunk
                write_msg(sys.stdout.buffer, json.loads(body))
        except Exception as e:
            write_msg(sys.stdout.buffer, {"error": str(e)})
            break


if __name__ == "__main__":
    main()
