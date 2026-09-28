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


def cmd_adr(args):
    """Список ADR из docs/adr/."""
    from pathlib import Path as _P
    adr_dir = _P(__file__).parent.parent / "docs" / "adr"
    files = sorted(adr_dir.glob("[0-9][0-9][0-9]-*.md"))
    if not files:
        print("ADR не найдены")
        return 1
    for f in files:
        try:
            first = f.read_text(encoding="utf-8").split("\n")[0]
            title = first.lstrip("# ").strip()
            print(f"  {f.stem[:3]}  {title}")
        except Exception:
            print(f"  {f.stem}")
    return 0


def cmd_agents(args):
    """Список зарегистрированных агентов."""
    from aura.bootstrap import build_orchestrator
    orch = build_orchestrator()
    reg = orch.registry
    if hasattr(reg, 'keys'):
        names = sorted(reg.keys())
    elif hasattr(reg, 'agents'):
        names = sorted(a.name for a in reg.agents)
    else:
        names = sorted(str(a) for a in reg)
    print(f"Всего агентов: {len(orch)}")
    print("-" * 40)
    for n in names:
        print(f"  {n}")
    return 0


def cmd_professions(args):
    """Список профессий из docs/professions.md."""
    from pathlib import Path as _P
    doc = _P(__file__).parent.parent / "docs" / "professions.md"
    if not doc.exists():
        print("docs/professions.md не найден")
        return 1
    text = doc.read_text(encoding="utf-8")
    # Считаем строки таблиц
    lines = [l for l in text.split("\n") if l.startswith("| ") and "Профессия" not in l and "---" not in l]
    print(f"Всего профессий: ~{len(lines)}")
    print("Документ:", doc)
    return 0


def cmd_wrappers(args):
    """Wrappers: list / status."""
    from aura.wrappers import get_registry
    reg = get_registry()
    action = getattr(args, "action", "list")
    if action == "list":
        names = reg.list_names()
        print(f"Wrappers: {len(names)}")
        for n in names:
            print(f"  {n}")
        return 0
    if action == "status":
        for st in reg.status_all():
            avail = "✅" if st.get("available") else "❌"
            print(f"  {avail} {st.get('name')}: {st}")
        return 0
    print(f"Неизвестное действие: {action}")
    return 1


def cmd_wrappers_hint(args):
    """Подсказка по установке wrapper'а."""
    hints = {
        "grbl": "pyserial + GRBL 1.1 прошивка. Порт: /dev/ttyUSB0 или /dev/ttyACM0",
        "blender": "Blender 4.2+. Запусти TCP-сервер: blender --python scripts/aura_server.py",
        "figma": "Figma token: export FIGMA_TOKEN=... или ~/.config/aura/figma_token",
    }
    name = getattr(args, "name", None)
    if name and name in hints:
        print(f"💡 {name}: {hints[name]}")
        return 0
    for k, v in hints.items():
        print(f"  {k}: {v}")
    return 0


def cmd_profile(args):
    """Voice Profiles: list / set / show."""
    from aura import voice_profiles as vp
    from aura import settings
    action = getattr(args, "action", "list")
    if action == "list":
        for p in vp.list_profiles():
            mark = "*" if p.name == settings.get("voice_profile", "default") else " "
            print(f"  {mark} {p.name:15s} rate={p.rate}  {p.description}")
        return 0
    if action == "set":
        name = getattr(args, "name", None)
        if not name or name not in vp.PROFILES:
            print(f"❌ Профиль {name!r}. Доступны: {list(vp.PROFILES.keys())}")
            return 1
        settings.set_value("voice_profile", name)
        print(f"✅ Профиль: {name}")
        return 0
    if action == "show":
        name = settings.get("voice_profile", "default")
        p = vp.get_profile(name)
        print(f"Активный: {p.name} ({p.style}, rate={p.rate})")
        return 0
    return 1


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
    sub.add_parser("adr", help="список ADR").set_defaults(func=cmd_adr)
    sub.add_parser("agents", help="список агентов").set_defaults(func=cmd_agents)
    sub.add_parser("professions", help="каталог профессий").set_defaults(func=cmd_professions)
    p_wrap = sub.add_parser("wrappers", help="сторонние приложения")
    p_wrap.add_argument("action", nargs="?", choices=["list", "status"], default="list")
    p_wrap.set_defaults(func=cmd_wrappers)
    p_hint = sub.add_parser("wrappers-hint", help="подсказка по wrapper")
    p_hint.add_argument("name", nargs="?", default=None)
    p_hint.set_defaults(func=cmd_wrappers_hint)
    p_prof = sub.add_parser("profile", help="voice profiles")
    p_prof.add_argument("action", nargs="?", choices=["list","set","show"], default="list")
    p_prof.add_argument("name", nargs="?", default=None)
    p_prof.set_defaults(func=cmd_profile)


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
