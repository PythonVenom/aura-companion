#!/usr/bin/env python3
"""aura_log — CLI для Logbook.

Использование:
    aura_log event <kind> <text>
    aura_log decision <key> <why> [--adr ADR-NNN]
    aura_log unresolved <what> [status]
    aura_log mood <text>
    aura_log today       # markdown за сегодня
    aura_log search [--tag T] [--kind K]
"""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from aura.core.logbook import Logbook


def main() -> int:
    p = argparse.ArgumentParser(prog="aura_log")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("event")
    e.add_argument("kind")
    e.add_argument("text")

    d = sub.add_parser("decision")
    d.add_argument("key")
    d.add_argument("why")
    d.add_argument("--adr", default=None)

    u = sub.add_parser("unresolved")
    u.add_argument("what")
    u.add_argument("status", nargs="?", default="")

    m = sub.add_parser("mood")
    m.add_argument("text")

    sub.add_parser("today")

    s = sub.add_parser("search")
    s.add_argument("--tag", default=None)
    s.add_argument("--kind", default=None)

    args = p.parse_args()
    lb = Logbook()

    if args.cmd == "event":
        lb.event(args.kind, args.text)
    elif args.cmd == "decision":
        lb.decision(args.key, args.why, adr=args.adr)
    elif args.cmd == "unresolved":
        lb.unresolved(args.what, args.status)
    elif args.cmd == "mood":
        lb.mood(args.text)
    elif args.cmd == "today":
        lb.write_markdown_today()
        print(lb.markdown_today())
    elif args.cmd == "search":
        for e in lb.search(tag=args.tag, kind=args.kind):
            print(e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
