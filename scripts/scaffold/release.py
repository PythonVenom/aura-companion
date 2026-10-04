#!/usr/bin/env python3
"""scaffold/release.py v4.0 "message" — release gate с evals."""
import argparse, subprocess, sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("tag")
ap.add_argument("message", nargs="?", default="")
a = ap.parse_args()

root = Path(__file__).resolve().parents[2]

def run(cmd, cwd=root):
    print(f"$ {cmd}")
    r = subprocess.run(cmd, shell=True, cwd=cwd)
    return r.returncode

print("=== 1/6 pytest ===")
if run("source venv/bin/activate && pytest -q 2>&1 | tail -2") != 0:
    print("❌ pytest"); sys.exit(1)

print("=== 2/6 evals ===")
rc = subprocess.run("source venv/bin/activate && python3 scripts/run_evals.py",
                    shell=True, cwd=root, capture_output=True, text=True)
print(rc.stdout.splitlines()[-1] if rc.stdout else "")
if rc.returncode != 0:
    print("❌ evals"); sys.exit(1)

print("=== 3/6 git clean ===")
rc = subprocess.run("git status --porcelain", shell=True, cwd=root,
                    capture_output=True, text=True)
if rc.stdout.strip():
    print("❌ грязный tree:"); print(rc.stdout); sys.exit(1)

print("=== 4/6 ADR index ===")
if run("source venv/bin/activate && pytest tests/test_adr_index.py -q 2>&1 | tail -1") != 0:
    print("❌ ADR index"); sys.exit(1)

print(f"=== 5/6 tag {a.tag} ===")
msg = a.message or f"Release {a.tag}"
run(f'git tag -a {a.tag} -m "{msg}"')

print("=== 6/6 push ===")
run("git push origin master")
run(f"git push origin {a.tag}")

print(f"\n✅ {a.tag} → {subprocess.run('git rev-parse --short HEAD', shell=True, cwd=root, capture_output=True, text=True).stdout.strip()}")
