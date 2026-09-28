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




def cmd_settings_reset(args):
    """Сбросить настройки к defaults."""
    from aura import settings
    settings.save(dict(settings.DEFAULTS))
    print("OK: настройки сброшены к defaults")
    print(json.dumps(settings.load(), indent=2, ensure_ascii=False))




def _parse_duration(s: str) -> int:
    """'30s'/'5m'/'2h' → секунды. Одна единица (YAGNI)."""
    import re
    m = re.fullmatch(r"(\d+)([smh])", s.strip().lower())
    if not m:
        raise ValueError(f"Формат: 30s, 5m, 2h (получено: {s!r})")
    n, unit = int(m.group(1)), m.group(2)
    return n * {"s": 1, "m": 60, "h": 3600}[unit]


def cmd_timer(args):
    from aura.agents import time_agent
    try:
        seconds = _parse_duration(args.duration)
    except ValueError as e:
        print(f"❌ {e}")
        return 1
    label = args.label or args.duration
    t = time_agent.add_timer(seconds, label)
    print(f"⏱ Таймер: {t['label']} (id={t['id']})")
    return 0


def cmd_reminder(args):
    from aura.agents import health
    item = health.add_reminder(args.text, args.every_minutes)
    print(f"💊 Напоминание каждые {args.every_minutes} мин: {item['text']}")
    return 0


def cmd_timers(args):
    from aura.agents import time_agent
    items = time_agent.list_pending()
    if not items:
        print("⏱ Активных таймеров нет")
        return 0
    import time
    now = time.time()
    for it in items:
        left = int(it["fire_at"] - now)
        print(f"  {it['label']:20s} через {left}s")
    return 0


def cmd_reminders(args):
    from aura.agents import health
    items = health.list_reminders()
    if not items:
        print("💊 Напоминаний нет")
        return 0
    import time
    now = time.time()
    for it in items:
        left = int(it.get("next_at", 0) - now)
        print(f"  {it['text'][:40]:40s} через {left}s (каждые {it['every_sec']//60}m)")
    return 0


def cmd_doctor(args):
    from aura.doctor import main as doctor_main
    return doctor_main()


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

    p_reset = sub.add_parser("settings-reset", help="сбросить настройки")
    p_reset.set_defaults(func=cmd_settings_reset)
    sub.add_parser("reload-extension", help="Firefox extension").set_defaults(func=cmd_reload_extension)
    sub.add_parser("doctor", help="диагностика одной командой").set_defaults(func=cmd_doctor)

    p_timer = sub.add_parser("timer", help="таймер: 30s / 5m / 2h")
    p_timer.add_argument("duration")
    p_timer.add_argument("label", nargs="?", default="")
    p_timer.set_defaults(func=cmd_timer)

    p_rem = sub.add_parser("reminder", help="напоминание каждые N мин")
    p_rem.add_argument("text")
    p_rem.add_argument("every_minutes", nargs="?", type=int, default=60)
    p_rem.set_defaults(func=cmd_reminder)

    sub.add_parser("timers", help="список активных таймеров").set_defaults(func=cmd_timers)
    sub.add_parser("reminders", help="список напоминаний").set_defaults(func=cmd_reminders)

    args = parser.parse_args()
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
