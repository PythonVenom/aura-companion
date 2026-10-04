#!/usr/bin/env python3
"""aura_plugin — CLI управления плагинами (ADR-090).

Использование:
    aura_plugin list
    aura_plugin install <path>
    aura_plugin remove <id>
    aura_plugin info <id>
"""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aura.core.plugin_manager import PluginManager


def cmd_list(args):
    m = PluginManager()
    plugins = m.list_plugins()
    if not plugins:
        print("Плагинов нет.")
        return 0
    print(f"Установлено: {len(plugins)}")
    for p in plugins:
        risk = "☁️ " if p.is_cloud else "🏠 "
        print(f"  {risk} {p.id:20} v{p.version:10} {p.name}")
    return 0


def cmd_install(args):
    m = PluginManager()
    src = Path(args.path).expanduser()
    if not src.is_dir():
        print(f"Нет директории: {src}")
        return 1
    # Читаем манифест заранее — показать риск
    try:
        from aura.core.plugin_manifest import load_manifest
        man = load_manifest(src)
    except Exception as e:
        print(f"Ошибка манифеста: {e}")
        return 1

    if man.needs_consent:
        print(f"⚠️  RISK WARNING: {man.id}")
        if man.is_cloud:
            print(f"    Данные уходят на {man.endpoint or 'внешний сервис'}")
        for w in man.warns:
            print(f"    - {w}")
        ans = input("Продолжить? [y/N]: ").strip().lower()
        if ans != "y":
            print("Отменено.")
            return 0

    try:
        installed = m.install(src)
        print(f"Установлен: {installed.id} v{installed.version}")
        return 0
    except FileExistsError as e:
        print(f"Уже установлен: {e}. Используй --force.")
        return 1


def cmd_remove(args):
    m = PluginManager()
    if m.remove(args.id):
        print(f"Удалён: {args.id}")
        return 0
    print(f"Не найден: {args.id}")
    return 1


def cmd_info(args):
    m = PluginManager()
    p = m.get(args.id)
    if p is None:
        print(f"Не найден: {args.id}")
        return 1
    print(f"id:       {p.id}")
    print(f"name:     {p.name}")
    print(f"version:  {p.version}")
    print(f"author:   {p.author}")
    print(f"risk:     {p.risk_level}")
    print(f"cloud:    {p.is_cloud}")
    print(f"endpoint: {p.endpoint or '—'}")
    print(f"warns:    {len(p.warns)}")
    for w in p.warns:
        print(f"  - {w}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="aura_plugin")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list").set_defaults(func=cmd_list)

    p_i = sub.add_parser("install")
    p_i.add_argument("path")
    p_i.add_argument("--force", action="store_true")
    p_i.set_defaults(func=cmd_install)

    p_r = sub.add_parser("remove")
    p_r.add_argument("id")
    p_r.set_defaults(func=cmd_remove)

    p_info = sub.add_parser("info")
    p_info.add_argument("id")
    p_info.set_defaults(func=cmd_info)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
