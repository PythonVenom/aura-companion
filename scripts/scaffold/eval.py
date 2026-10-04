#!/usr/bin/env python3
"""scaffold/eval.py "включи нирвану" music.play query=Nirvana

Добавляет кейс в evals/golden.yaml (идемпотентно).
"""
import argparse, sys, yaml
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("input")
ap.add_argument("route_action", help="music.play")
ap.add_argument("args", nargs="*", help="key=value")
a = ap.parse_args()

root = Path(__file__).resolve().parents[2]
golden = root / "evals/golden.yaml"
data = yaml.safe_load(golden.read_text(encoding="utf-8")) if golden.exists() else {"cases": []}

route, action = a.route_action.split(".", 1) if "." in a.route_action else (a.route_action, "")
for c in data["cases"]:
    if c.get("input") == a.input:
        print(f"[skip] '{a.input}' уже есть"); sys.exit(0)

case = {"input": a.input, "route": route}
if action: case["action"] = action
args = {}
for kv in a.args:
    if "=" in kv:
        k, v = kv.split("=", 1)
        args[k] = v
if args: case["args"] = args

data["cases"].append(case)
golden.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
                  encoding="utf-8")
print(f"[ok] +1 кейс. Всего: {len(data['cases'])}")
