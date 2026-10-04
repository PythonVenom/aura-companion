"""Aura health v0.1 — read-only диагностика.

ADR-050: НЕ чинит, НЕ рестартит, НЕ пишет в файлы Aura.
Запуск: python3 scripts/aura_health.py
"""
import re
import subprocess
import sys
from pathlib import Path


def parse_thread_count(pid: int) -> int:
    return len(list(Path(f"/proc/{pid}/task").iterdir()))


def detect_thread_leak(t0: int, t1: int) -> bool:
    return t1 > t0


def parse_cpu_from_top(line: str) -> float:
    m = re.search(r"\s(\d+[.,]\d+)\s+\d+[.,]\d+\s", line)
    if not m:
        raise ValueError(f"cannot parse CPU from: {line!r}")
    return float(m.group(1).replace(",", "."))


def parse_audio_sources(pactl_output: str) -> dict:
    sources = []
    default_running = False
    for line in pactl_output.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        sid, name = parts[0], parts[1]
        state = parts[-1] if parts[-1] in ("RUNNING", "IDLE", "SUSPENDED") else ""
        sources.append({"id": sid, "name": name, "state": state})
        if "echo-cancel-source" in name and state == "RUNNING":
            default_running = True
    return {"default_running": default_running, "sources": sources}


def sh(cmd: list) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return ""


def find_pid() -> int | None:
    out = sh(["pgrep", "-f", "aura_main"]).strip().splitlines()
    return int(out[0]) if out else None


def systemd_state() -> str:
    return sh(["systemctl", "--user", "is-active", "aura"]).strip() or "unknown"


def cpu_delta(pid: int) -> float:
    out = sh(["top", "-b", "-n", "2", "-d", "3", "-p", str(pid)])
    lines = [l for l in out.splitlines() if l.strip().startswith(str(pid))]
    if len(lines) < 2:
        return -1.0
    return parse_cpu_from_top(lines[-1])


def audio_state() -> dict:
    out = sh(["pactl", "list", "short", "sources"])
    return parse_audio_sources(out)


def journal_errors() -> list:
    out = sh(["journalctl", "--user", "-u", "aura", "-n", "80",
              "--no-pager", "--output=cat"])
    pattern = re.compile(r"error|warn|traceback|exception", re.I)
    return [l for l in out.splitlines() if pattern.search(l)][-10:]


def main() -> int:
    print("=== Aura health v0.1 (read-only) ===\n")
    pid = find_pid()
    if not pid:
        print("🔴 aura_main: NOT RUNNING")
        return 1

    state = systemd_state()
    icon = "✅" if state == "active" else "🔴"
    print(f"{icon} systemd: {state}   pid={pid}")

    threads = parse_thread_count(pid)
    print(f"📊 threads: {threads}")

    cpu = cpu_delta(pid)
    cpu_icon = "🔴" if cpu > 30 else ("⚠️" if cpu > 10 else "✅")
    print(f"{cpu_icon} cpu: {cpu:.1f}%")

    au = audio_state()
    au_icon = "✅" if au["default_running"] else "🔴"
    print(f"{au_icon} audio default (echo-cancel-source): "
          f"{'RUNNING' if au['default_running'] else 'NOT RUNNING'}")

    errs = journal_errors()
    if errs:
        print(f"🔴 journal errors: {len(errs)}")
        for e in errs:
            print(f"   {e[:100]}")
    else:
        print("✅ journal: clean")

    print("\n=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
