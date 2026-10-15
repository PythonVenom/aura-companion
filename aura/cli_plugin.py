"""CLI для плагинов AURA (магазин).

Использование:
    python -m aura.cli_plugin list
    python -m aura.cli_plugin install <name>
    python -m aura.cli_plugin template <name> [author]
    python -m aura.cli_plugin stats
"""
from __future__ import annotations

import argparse
import sys

from aura.core.plugin_sdk import get_sdk


def cmd_list(args) -> int:
    sdk = get_sdk()
    plugins = sdk.list_plugins()
    if not plugins:
        print("Плагинов нет.")
        return 0
    print(f"📦 Плагинов: {len(plugins)}")
    for p in plugins:
        print(f"  • {p.name:20s} v{p.version:8s} [{p.author}]")
        if p.description:
            print(f"    {p.description}")
    return 0


def cmd_install(args) -> int:
    sdk = get_sdk()
    # Заглушка: установка из локального каталога
    from pathlib import Path
    src = Path(args.name)
    if not src.exists():
        print(f"❌ Не найдено: {src}")
        return 1
    print(f"📥 Установка из {src}...")
    return 0


def cmd_template(args) -> int:
    sdk = get_sdk()
    path = sdk.install_template(args.name, author=args.author or "unknown")
    print(f"✅ Шаблон создан: {path}")
    print(f"   Отредактируй {path}/plugin.py и {path}/manifest.json")
    return 0


def cmd_stats(args) -> int:
    sdk = get_sdk()
    s = sdk.stats()
    print(f"📁 Каталог: {s['dir']}")
    print(f"📦 Плагинов: {s['count']}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="aura-plugin", description="Магазин плагинов AURA")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="список установленных").set_defaults(func=cmd_list)
    sub.add_parser("stats", help="статистика").set_defaults(func=cmd_stats)

    p_inst = sub.add_parser("install", help="установить плагин")
    p_inst.add_argument("name", help="путь к плагину")
    p_inst.set_defaults(func=cmd_install)

    p_tpl = sub.add_parser("template", help="создать шаблон")
    p_tpl.add_argument("name", help="имя плагина")
    p_tpl.add_argument("--author", help="автор")
    p_tpl.set_defaults(func=cmd_template)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
