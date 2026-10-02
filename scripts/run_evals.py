#!/usr/bin/env python3
"""run_evals.py — прогоняет golden dataset через RouteTree."""
import sys, yaml
from pathlib import Path

def main():
    root = Path(__file__).resolve().parents[1]
    data = yaml.safe_load((root / "evals/golden.yaml").read_text(encoding="utf-8"))
    cases = data["cases"]

    sys.path.insert(0, str(root))
    from aura.core.route_tree import build_route_tree
    rt = build_route_tree()

    passed = failed = 0
    fails = []
    for c in cases:
        inp = c["input"]
        exp_route = c.get("route")
        exp_action = c.get("action")
        r = rt.handle(inp, {})
        ok = True
        if not r or r.get("route") != exp_route:
            ok = False
        if exp_action and r and r.get("action") != exp_action:
            ok = False
        for key, val in (c.get("args") or {}).items():
            if key.endswith("_has"):
                field = key[:-4]
                got = (r or {}).get("args", {}).get(field, "")
                if val.lower() not in str(got).lower():
                    ok = False
        if ok:
            passed += 1
        else:
            failed += 1
            fails.append((inp, exp_route, exp_action, r))

    total = passed + failed
    print(f"EVALS: {passed}/{total} passed ({100*passed//total}%)")
    for inp, er, ea, got in fails[:10]:
        print(f"  FAIL {inp!r}: expected {er}.{ea}, got {got}")

    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
