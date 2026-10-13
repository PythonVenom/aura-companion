"""DBus API для Aura (GAPS #38).

Интерфейс: org.aura.Companion
Путь:      /org/aura/Companion

Методы:
  Chat(text) -> text         — отправить сообщение, получить ответ
  Status() -> json            — статус сервиса
  Agents() -> json            — список агентов
  Command(cmd) -> json        — выполнить команду ядра

Сигналы:
  MessageReceived(user, aura) — пришло новое сообщение
  StatusChanged(status)       — изменился статус

Наука:
- freedesktop.org DBus Specification (2003)
- jeepney — чистый Python DBus
- BlueZ / NetworkManager — образцы D-Bus сервисов

Запуск:
  aura-dbus (или python -m aura.core.dbus_service)
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

try:
    from jeepney import (
        DBusAddress, new_method_call, new_method_return, MessageType,
    )
    from jeepney.bus_messages import message_bus
    from jeepney.io.asyncio import open_dbus_connection
    JEEPNEY_OK = True
except ImportError as _e:
    import sys
    print(f"❌ jeepney import: {_e}", file=sys.stderr)
    JEEPNEY_OK = False


# === Адрес сервиса ===
BUS_NAME = "org.aura.Companion"
OBJECT_PATH = "/org/aura/Companion"
INTERFACE = "org.aura.Companion"

# === Кэш ===
CACHE = Path.home() / ".cache" / "aura"


class AuraDBusService:
    """DBus сервис Aura."""

    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self._conn = None
        self._running = False

    async def start(self):
        """Запустить сервис."""
        if not JEEPNEY_OK:
            print("❌ jeepney не установлен: pip install jeepney", file=sys.stderr)
            return 1

        self._conn = await open_dbus_connection(bus="SESSION")
        self._running = True

        # Регистрация имени
        try:
            # RequestName через message_bus
            # jeepney 0.9.0: используем conn.send() + conn.receive()
            req = new_method_call(
                message_bus,
                "RequestName",
                "su",
                (BUS_NAME, 0),
            )
            await self._conn.send(req)
            # Читаем reply (ждём до 2 сек)
            try:
                reply = await asyncio.wait_for(
                    self._conn.receive(), timeout=2.0,
                )
                print(f"✅ DBus: {BUS_NAME} зарегистрирован", flush=True)
            except asyncio.TimeoutError:
                print(f"⚠️ DBus: RequestName timeout, продолжаю", flush=True)
        except Exception as e:
            print(f"⚠️ RequestName: {e}", file=sys.stderr)

        # Экспорт объектов — через встроенный механизм jeepney
        # Для простоты: обработка запросов через входящие сообщения
        await self._serve_loop()

    async def _serve_loop(self):
        """Главный цикл: читаем входящие сообщения."""
        while self._running:
            try:
                msg = await asyncio.wait_for(
                    self._conn.receive(), timeout=1.0,
                )
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"⚠️ DBus receive: {e}", file=sys.stderr)
                break

            if msg is None:
                break
            if msg.header.message_type == MessageType.method_call:
                await self._handle_method(msg)

    async def _handle_method(self, msg):
        """Обработать method_call."""
        # В jeepney fields — dict-like
        try:
            member = msg.header.fields[3]  # MEMBER (3)
        except (KeyError, IndexError):
            return  # Не наш метод

        try:
            body = msg.body
            if member == "Chat":
                text = body[0] if body else ""
                reply_text = await self._chat(text)
                await self._reply(msg, "s", (reply_text,))
            elif member == "Status":
                data = self._status()
                await self._reply(msg, "s", (json.dumps(data, ensure_ascii=False),))
            elif member == "Agents":
                data = self._agents()
                await self._reply(msg, "s", (json.dumps(data, ensure_ascii=False),))
            elif member == "Command":
                cmd = body[0] if body else ""
                data = await self._command(cmd)
                await self._reply(msg, "s", (json.dumps(data, ensure_ascii=False),))
            elif member == "Ping":
                await self._reply(msg, "s", ("pong",))
            else:
                await self._error(msg, f"Unknown method: {member}")
        except Exception as e:
            await self._error(msg, str(e))

    async def _reply(self, msg, signature: str, body: tuple):
        """Ответить на method_call (jeepney new_reply)."""
        try:
            reply = new_method_return(msg, signature=signature, body=body)
            await self._conn.send(reply)
        except Exception as e:
            print(f"⚠️ reply: {e}", file=sys.stderr)

    async def _error(self, msg, text: str):
        """Ответить ошибкой."""
        await self._reply(msg, "s", (f"error: {text}",))

    # === Бизнес-логика ===

    async def _chat(self, text: str) -> str:
        """Отправить сообщение в ChatBridge + подождать ответ."""
        if not text.strip():
            return "❌ Пустое сообщение"

        inbox = CACHE / "chat_inbox.jsonl"
        history = CACHE / "chat_history.jsonl"
        inbox.parent.mkdir(parents=True, exist_ok=True)

        offset = history.stat().st_size if history.exists() else 0
        ts = time.time()

        with open(inbox, "a", encoding="utf-8") as f:
            f.write(json.dumps({"user": text, "ts": ts}, ensure_ascii=False) + chr(10))
            f.flush()
            os.fsync(f.fileno())

        # Ждём ответа до 30 сек
        deadline = time.time() + 30
        while time.time() < deadline:
            if history.exists() and history.stat().st_size > offset:
                with open(history, encoding="utf-8") as f:
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
            await asyncio.sleep(0.3)
        return "⏱ Aura не ответила за 30с"

    def _status(self) -> dict:
        """Статус сервиса."""
        out = {"status": "ok", "ts": time.time()}
        try:
            import subprocess
            r = subprocess.run(
                ["systemctl", "--user", "is-active", "aura.service"],
                capture_output=True, text=True, timeout=2,
            )
            out["service"] = r.stdout.strip()
        except Exception:
            out["service"] = "unknown"
        return out

    def _agents(self) -> dict:
        """Список агентов."""
        if self.orchestrator is None:
            try:
                from aura.bootstrap import build_orchestrator
                self.orchestrator = build_orchestrator()
            except Exception as e:
                return {"error": str(e), "agents": []}
        try:
            names = sorted(self.orchestrator.registry.list_names())
            return {"agents": names, "count": len(names)}
        except Exception as e:
            return {"error": str(e), "agents": []}

    async def _command(self, cmd: str) -> dict:
        """Выполнить CLI-команду ядра."""
        import subprocess
        try:
            r = subprocess.run(
                [sys.executable, "-m", "aura.cli", *cmd.split()],
                capture_output=True, text=True, timeout=15,
            )
            return {
                "ok": r.returncode == 0,
                "stdout": r.stdout[:2000],
                "stderr": r.stderr[:500],
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def stop(self):
        self._running = False


async def main():
    service = AuraDBusService()
    try:
        await service.start()
    except KeyboardInterrupt:
        print("\n🛸 DBus: shutdown", flush=True)
        service.stop()


if __name__ == "__main__":
    asyncio.run(main())
