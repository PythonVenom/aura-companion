"""CLI для отладки Ауры.

Использование:
    python -m aura.cli check         — system_check
    python -m aura.cli health        — health endpoint
    python -m aura.cli logs          — последние 20 строк лога
    python -m aura.cli calendar      — календарь
    python -m aura.cli status        — статус сервиса
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def cmd_check(args):
    from aura.system_check import format_report
    print(format_report())


def cmd_health(args):
    """Health check: JSON для мониторинга."""
    out = {"status": "ok", "components": {}}

    # systemd
    try:
        r = subprocess.run(["systemctl", "--user", "is-active", "aura.service"],
                           capture_output=True, text=True, timeout=2)
        out["components"]["service"] = r.stdout.strip()
    except Exception:
        out["components"]["service"] = "unknown"

    # FSM
    fsm_path = Path("/tmp/aura_fsm.json")
    if fsm_path.exists():
        try:
            data = json.loads(fsm_path.read_text())
            out["components"]["fsm"] = data.get("state", "idle")
        except Exception:
            out["components"]["fsm"] = "error"
    else:
        out["components"]["fsm"] = "idle"

    # Calendar
    cal_path = Path("/tmp/aura_calendar.json")
    if cal_path.exists():
        try:
            out["components"]["calendar_events"] = len(json.loads(cal_path.read_text()))
        except Exception:
            out["components"]["calendar_events"] = 0
    else:
        out["components"]["calendar_events"] = 0

    # Overall
    if out["components"].get("service") != "active":
        out["status"] = "degraded"

    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out["status"] == "ok" else 1


def cmd_logs(args):
    try:
        r = subprocess.run(
            ["journalctl", "--user", "-u", "aura.service",
             "-n", str(args.n), "--no-pager"],
            capture_output=True, text=True, timeout=5)
        print(r.stdout)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)


def cmd_calendar(args):
    from aura.agents import chat_sense
    items = chat_sense.get_today()
    if not items:
        print("Календарь пуст")
        return
    for e in items:
        print(f"  {e.get('when', '')[:16]} — {e.get('chat', '')}: {e.get('text', '')[:60]}")


def cmd_status(args):
    try:
        r = subprocess.run(
            ["systemctl", "--user", "status", "aura.service", "--no-pager"],
            capture_output=True, text=True, timeout=3)
        print(r.stdout[:2000])
    except Exception as e:
        print(f"error: {e}")


def cmd_reload_extension(args):
    print("Открой about:debugging#/runtime/this-firefox")
    print("Aura Bridge → Remove → Load Temporary Add-on → manifest.json")




def cmd_watch(args):
    """Мониторинг health в реальном времени (каждые N сек)."""
    import time
    try:
        while True:
            print("\033[2J\033[H", end="")  # clear screen
            print(f"=== Aura health — {time.strftime('%H:%M:%S')} ===")
            cmd_health(args)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nСтоп.")




def cmd_settings(args):
    """Показать/изменить настройки."""
    from aura import settings
    if args.action == 'show' or args.action is None:
        print(json.dumps(settings.load(), indent=2, ensure_ascii=False))
    elif args.action == 'get' and args.key:
        print(settings.get(args.key))
    elif args.action == 'set' and args.key and args.value:
        settings.set_value(args.key, args.value)
        print(f'OK: {args.key} = {args.value}')
    else:
        print('Использование: settings [show|get KEY|set KEY VALUE]')


def main():
    parser = argparse.ArgumentParser(prog="aura", description="Aura CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="system_check").set_defaults(func=cmd_check)
    sub.add_parser("health", help="health JSON").set_defaults(func=cmd_health)

    p_logs = sub.add_parser("logs", help="логи сервиса")
    p_logs.add_argument("-n", type=int, default=20)
    p_logs.set_defaults(func=cmd_logs)

    sub.add_parser("calendar", help="календарь на сегодня").set_defaults(func=cmd_calendar)
    sub.add_parser("status", help="systemd status").set_defaults(func=cmd_status)

    p_watch = sub.add_parser("watch", help="health в реальном времени")
    p_watch.add_argument("-i", "--interval", type=int, default=5)
    p_watch.set_defaults(func=cmd_watch)

    p_set = sub.add_parser("settings", help="настройки")
    p_set.add_argument("action", nargs="?", choices=["show", "get", "set"], default="show")
    p_set.add_argument("key", nargs="?", default=None)
    p_set.add_argument("value", nargs="?", default=None)
    p_set.set_defaults(func=cmd_settings)
    sub.add_parser("reload-extension", help="Firefox extension").set_defaults(func=cmd_reload_extension)

    args = parser.parse_args()
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
