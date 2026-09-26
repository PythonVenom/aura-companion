#!/usr/bin/env python3
"""
Aura Firefox Host — native messaging host
Мост: Firefox <-> Unix socket <-> Аура
"""

import sys
import os
import json
import struct
import socket
import threading
import time


SOCKET_PATH = "/tmp/aura_firefox.sock"


def read_message():
    """Читать сообщение из stdin (native messaging)"""
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) == 0:
        return None
    if len(raw_length) != 4:
        return None
    length = struct.unpack('@I', raw_length)[0]
    data = sys.stdin.buffer.read(length)
    if len(data) != length:
        return None
    return json.loads(data.decode('utf-8'))


def send_message(msg):
    """Отправить сообщение в stdout (Firefox)"""
    data = json.dumps(msg, ensure_ascii=False).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('@I', len(data)))
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


# Очередь запросов к Firefox
pending = {}
pending_lock = threading.Lock()
next_id = [0]


def socket_server():
    """Unix socket сервер для Ауры"""
    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    os.chmod(SOCKET_PATH, 0o600)
    server.listen(1)

    print(f"[Host] Socket сервер: {SOCKET_PATH}", file=sys.stderr)

    while True:
        try:
            conn, _ = server.accept()
            threading.Thread(target=handle_aura, args=(conn,), daemon=True).start()
        except Exception as e:
            print(f"[Host] Accept error: {e}", file=sys.stderr)


def handle_aura(conn):
    """Обработка запросов от Ауры"""
    buffer = b""
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            buffer += data

            # Парсим: 4 байта длины + JSON
            while len(buffer) >= 4:
                length = struct.unpack('@I', buffer[:4])[0]
                if len(buffer) < 4 + length:
                    break
                msg = json.loads(buffer[4:4+length].decode('utf-8'))
                buffer = buffer[4+length:]

                # Отправляем в Firefox
                with pending_lock:
                    msg_id = next_id[0]
                    next_id[0] += 1
                    msg['id'] = msg_id
                    pending[msg_id] = conn

                send_message(msg)

    except Exception as e:
        print(f"[Host] Aura error: {e}", file=sys.stderr)
    finally:
        conn.close()


def firefox_reader():
    """Читать ответы от Firefox"""
    while True:
        msg = read_message()
        if msg is None:
            print("[Host] Firefox closed", file=sys.stderr)
            break

        # Уведомление от content script — писать в файл.
        if msg.get('action') == 'max_new_message':
            try:
                import pathlib as _pl
                _pl.Path('/tmp/aura_new_message.json').write_text(
                    json.dumps(msg, ensure_ascii=False), encoding='utf-8'
                )
            except Exception:
                pass
            continue

        msg_id = msg.get('id')
        with pending_lock:
            conn = pending.pop(msg_id, None)

        if conn:
            try:
                data = json.dumps(msg, ensure_ascii=False).encode('utf-8')
                conn.sendall(struct.pack('@I', len(data)) + data)
            except Exception as e:
                print(f"[Host] Send error: {e}", file=sys.stderr)


def main():
    # Запускаем socket сервер в фоне
    threading.Thread(target=socket_server, daemon=True).start()
    # Читаем ответы Firefox
    firefox_reader()


if __name__ == "__main__":
    main()
