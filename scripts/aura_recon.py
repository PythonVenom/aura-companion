#!/usr/bin/env python3
"""aura_recon — прогнать .tasks файл и собрать отчёт.

Запуск: python3 scripts/aura_recon.py <tag> [--clip]
Или: python3 -m scripts.aura_recon <tag>
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from aura.core.recon import parse_tasks  # noqa: E402

TASKS_DIR = Path(__file__).parent / "recon_tasks"
OUT_DIR = Path.home() / "aura_private" / "recon"
TIMEOUT = 10


def run_cmd(cmd: str) -> tuple:
    """Вернуть (exit_code, output)."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=TIMEOUT,
        )
        out = (r.stdout or "") + (r.stderr or "")
        return r.returncode, out.rstrip()
    except subprocess.TimeoutExpired:
        return 124, f"[timeout {TIMEOUT}s]"
    except Exception as e:
        return 1, f"[error: {e}]"


def run_file(path: str) -> str:
    p = Path(path).expanduser()
    if not p.exists():
        return "[missing]"
    try:
        return p.read_text(encoding="utf-8").rstrip()
    except Exception as e:
        return f"[read error: {e}]"


def format_report(tag: str, blocks: list) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out = [f"# Recon report: {tag}", f"# {ts}", ""]
    for b in blocks:
        out.append(f"## [{b.id}] {b.name}")
        for kind, payload in b.entries:
            if kind == "cmd":
                code, text = run_cmd(payload)
                out.append(f"$ {payload}")
                out.append(f"[exit={code}]")
                out.append(text)
                out.append("")
            elif kind == "file":
                out.append(f"$ cat {payload}")
                out.append(run_file(payload))
                out.append("")
        out.append("---")
        out.append("")
    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser(prog="aura_recon")
    p.add_argument("tag", help="имя .tasks файла без расширения")
    p.add_argument("--clip", action="store_true", help="копировать в clipboard (wl-copy)")
    p.add_argument("--out", help="куда писать (по умолчанию ~/aura_private/recon/)")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    tasks_file = TASKS_DIR / f"{args.tag}.tasks"
    if not tasks_file.exists():
        print(f"Нет файла: {tasks_file}", file=sys.stderr)
        return 2

    text = tasks_file.read_text(encoding="utf-8")
    blocks = parse_tasks(text)
    if not blocks:
        print(f"Пустой .tasks: {tasks_file}", file=sys.stderr)
        return 3

    report = format_report(args.tag, blocks)

    if args.out:
        out_path = Path(args.out).expanduser()
    else:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = OUT_DIR / f"{ts}_{args.tag}.md"

    out_path.write_text(report, encoding="utf-8")

    if args.clip:
        try:
            subprocess.run(["wl-copy"], input=report, text=True, timeout=5)
        except Exception as e:
            print(f"wl-copy fail: {e}", file=sys.stderr)

    if not args.quiet:
        print(report)
        print(f"\n[written to {out_path}]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
