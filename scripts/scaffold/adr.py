#!/usr/bin/env python3
"""scaffold/adr.py "Title" [--status Proposed] [--body "..."]"""
import argparse, re
from pathlib import Path

def next_num(d):
    nums = [int(p.stem[:3]) for p in d.glob("[0-9][0-9][0-9]-*.md")]
    return max(nums) + 1 if nums else 1

def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

ap = argparse.ArgumentParser()
ap.add_argument("title")
ap.add_argument("--status", default="Proposed")
ap.add_argument("--body", default="")
a = ap.parse_args()

root = Path(__file__).resolve().parents[2]
adr_dir = root / "docs/adr"
num = f"{next_num(adr_dir):03d}"
path = adr_dir / f"{num}-{slug(a.title)}.md"
if path.exists():
    print(f"[skip] {path.name}"); raise SystemExit

body = a.body or "## Контекст\n\n## Решение\n\n## Последствия\n\n"
path.write_text(
    f"# ADR-{num}: {a.title}\n\n**Статус:** {a.status}\n**Дата:** 2026-10-02\n\n{body}",
    encoding="utf-8")
idx = adr_dir / "README.md"
t = idx.read_text(encoding="utf-8")
if f"| {num} " not in t:
    t = t.rstrip("\n") + f"\n| {num} | {a.title} | {a.status} |\n"
    idx.write_text(t, encoding="utf-8")
print(f"[ok] docs/adr/{path.name}")
