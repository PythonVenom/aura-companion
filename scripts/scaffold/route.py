#!/usr/bin/env python3
"""scaffold/route.py vk.navigate --keywords "вк,вконтакте" --action navigate

Создаёт RouteTree leaf + тесты. НЕ трогает существующие листья.
"""
import argparse, re, sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("route", help="vk.navigate")
ap.add_argument("--keywords", required=True, help="вк,вконтакте,vk")
ap.add_argument("--action", default="navigate")
a = ap.parse_args()

route_name, _ = a.route.split(".", 1) if "." in a.route else (a.route, a.action)
root = Path(__file__).resolve().parents[2]
rt_path = root / "aura/core/route_tree.py"
t = rt_path.read_text(encoding="utf-8")

func_name = f"_build_{route_name}_leaf"
if func_name in t:
    print(f"[skip] {func_name} уже есть")
    sys.exit(0)

keywords = [k.strip() for k in a.keywords.split(",")]
kw_repr = ", ".join(f'"{k}"' for k in keywords)

new_leaf = f'''

def {func_name}():
    def action(t, c):
        return {{"route": "{route_name}", "action": "{a.action}", "args": {{}}}}
    return Leaf(
        "{route_name}",
        match=lambda t, c: _has(t, {kw_repr}),
        action=action,
    )
'''

# вставить leaf перед _build_ask_leaf
marker = "\ndef _build_ask_leaf():"
if marker not in t:
    print("[fail] _build_ask_leaf не найден"); sys.exit(1)
t = t.replace(marker, new_leaf + marker, 1)

# добавить в Selector
old_sel_line = "        _build_ask_leaf(),"
new_sel_line = f"        {func_name}(),\n        _build_ask_leaf(),"
if old_sel_line in t:
    t = t.replace(old_sel_line, new_sel_line, 1)

rt_path.write_text(t, encoding="utf-8")
print(f"[ok] leaf {route_name} → {rt_path.relative_to(root)}")

# тест
tests_dir = root / "tests"
tpath = tests_dir / f"test_route_{route_name}.py"
tpath.write_text(f'''"""Тесты для route {route_name}."""
from aura.core.route_tree import build_route_tree


def test_{route_name}_triggers():
    rt = build_route_tree()
    r = rt.handle("{keywords[0]}", {{}})
    assert r and r["route"] == "{route_name}"


def test_{route_name}_fallback():
    rt = build_route_tree()
    r = rt.handle("xyzzy-trigger-no", {{}})
    assert not r or r.get("route") != "{route_name}"
''', encoding="utf-8")
print(f"[ok] {tpath.relative_to(root)}")
print(f"     pytest {tpath.relative_to(root)} -q")
