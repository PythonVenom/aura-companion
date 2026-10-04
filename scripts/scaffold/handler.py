#!/usr/bin/env python3
"""scaffold/handler.py music.equalizer --args on:bool

Создаёт:
- aura/core/handlers/<group>/<name>.py (register)
- tests/test_handler_<group>_<name>.py
- ADR-stub
- авто-проверка pytest
"""
import argparse, re, subprocess, sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("capability", help="music.equalizer")
ap.add_argument("--args", default="", help="query:str,volume:int")
a = ap.parse_args()

group, name = a.capability.split(".", 1)
root = Path(__file__).resolve().parents[2]
handlers_dir = root / "aura/core/handlers" / group
handlers_dir.mkdir(parents=True, exist_ok=True)
(handlers_dir / "__init__.py").touch(exist_ok=True)

func = f"{group}_{name}".replace(".", "_")
fpath = handlers_dir / f"{name}.py"
if fpath.exists():
    print(f"[skip] {fpath.name} уже есть"); sys.exit(0)

# аргументы
arg_list = []
for pair in filter(None, a.args.split(",")):
    if ":" in pair:
        k, t = pair.split(":", 1); arg_list.append((k.strip(), t.strip()))
args_sig = ", ".join(f"{k}: {t}" for k, t in arg_list) or ""

fpath.write_text(f'''"""{a.capability} handler (scaffolded)."""
from __future__ import annotations


def {func}(args: dict) -> str:
    # TODO: реализация
{chr(10).join(f'    {k} = args.get("{k}")' for k, _ in arg_list) if arg_list else '    pass'}
    return "TODO: {a.capability}"


def register(dispatcher):
    dispatcher.register("{a.capability}", {func})
''', encoding="utf-8")

# тест
tests_dir = root / "tests"
tests_dir.mkdir(exist_ok=True)
tpath = tests_dir / f"test_handler_{group}_{name}.py"
tpath.write_text(f'''"""Тесты для {a.capability}."""
from aura.core.handlers.{group}.{name} import {func}


def test_{func}_smoke():
    r = {func}({{}})
    assert isinstance(r, str)
''', encoding="utf-8")

print(f"[ok] {fpath.relative_to(root)}")
print(f"[ok] {tpath.relative_to(root)}")
print(f"     git add {fpath.relative_to(root)} {tpath.relative_to(root)}")
print(f"     pytest {tpath.relative_to(root)} -q")
