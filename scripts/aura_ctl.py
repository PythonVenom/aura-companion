#!/usr/bin/env python3
"""Aura Control — CLI управления Aura (systemd + flag-файлы)."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


CACHE_DIR = Path(os.environ.get("AURA_CACHE_DIR", str(Path.home() / ".cache/aura")))
PAUSE_FLAG = CACHE_DIR / "aura_pause.flag"
STATUS_FILE = CACHE_DIR / "aura_status.json"
SERVICE = "aura.service"


def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def _notify(title, body, icon="audio-input-microphone"):
    try:
        subprocess.run(["notify-send", "-i", icon, title, body],
                       capture_output=True, text=True, timeout=2)
    except Exception:
        pass


def cmd_pause(args):
    PAUSE_FLAG.parent.mkdir(parents=True, exist_ok=True)
    PAUSE_FLAG.touch()
    _notify("Аура", "⏸ На паузе", "media-playback-pause")
    print("paused")
    return 0


def cmd_resume(args):
    PAUSE_FLAG.unlink(missing_ok=True)
    _notify("Аура", "▶ Слушает")
    print("resumed")
    return 0


def cmd_restart(args):
    _run(["systemctl", "--user", "restart", SERVICE])
    print("restarted")
    return 0


def cmd_stop(args):
    _run(["systemctl", "--user", "stop", SERVICE])
    print("stopped")
    return 0


def cmd_kill(args):
    _run(["systemctl", "--user", "kill", "-s", "SIGKILL", SERVICE])
    print("killed")
    return 0


def cmd_status(args):
    if STATUS_FILE.exists():
        try:
            data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            data = {"state": "error", "text": "parse: " + str(e)}
    else:
        data = {"state": "unknown", "text": ""}

    r = _run(["systemctl", "--user", "is-active", SERVICE])
    data["service"] = (r.stdout or "").strip() or "unknown"

    if getattr(args, "json", False):
        print(json.dumps(data, ensure_ascii=False))
    else:
        print("state:   " + str(data.get("state")))
        print("service: " + str(data.get("service")))
        print("text:    " + (data.get("text") or "—"))
    return 0


def main():
    p = argparse.ArgumentParser(prog="aura_ctl")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pause").set_defaults(func=cmd_pause)
    sub.add_parser("resume").set_defaults(func=cmd_resume)
    sub.add_parser("restart").set_defaults(func=cmd_restart)
    sub.add_parser("stop").set_defaults(func=cmd_stop)
    sub.add_parser("kill").set_defaults(func=cmd_kill)
    p_status = sub.add_parser("status")
    p_status.add_argument("--json", action="store_true")
    p_status.set_defaults(func=cmd_status)
    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
