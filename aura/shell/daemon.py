"""Aura Shell Daemon — управляет панелью, виджетами, темами.

Наука: Observer Pattern (GoF) + D-Bus (freedesktop).
Архитектура:
  ShellDaemon (Python) → D-Bus → Widgets (QML) → Polybar

Коллекторы: CPU, RAM, GPU, temp, Aura status.
События: resource_changed, aura_state_changed, chat_message.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

log = logging.getLogger("aura.shell.daemon")

CACHE = Path.home() / ".cache" / "aura"
SHELL_STATE = CACHE / "shell_state.json"


@dataclass
class ResourceSnapshot:
    ts: float = field(default_factory=lambda: datetime.now(UTC).timestamp())
    cpu_load: float = 0.0
    cpu_cores: int = 0
    cpu_temp_c: float | None = None
    ram_used_mb: int = 0
    ram_total_mb: int = 0
    swap_used_mb: int = 0
    disk_used_pct: float = 0.0
    gpu_name: str = ""
    gpu_util: int | None = None
    gpu_mem_used_mb: int | None = None


@dataclass
class AuraSnapshot:
    state: str = "unknown"      # idle | listening | thinking | speaking | paused | error
    text: str = ""
    voice: str = "irina"
    services: dict = field(default_factory=dict)


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout.strip()
    except Exception:
        return ""


def collect_resources() -> ResourceSnapshot:
    snap = ResourceSnapshot()
    try:
        snap.cpu_load = float(Path("/proc/loadavg").read_text().split()[0])
        snap.cpu_cores = os.cpu_count() or 1
    except Exception:
        pass
    try:
        mem = _run(["bash", "-c", "free -m | awk '/^Mem:/ {print $2, $3}'"])
        if mem:
            parts = mem.split()
            snap.ram_total_mb = int(parts[0])
            snap.ram_used_mb = int(parts[1])
    except Exception:
        pass
    try:
        sw = _run(["bash", "-c", "free -m | awk '/^Swap:/ {print $3}'"])
        if sw:
            snap.swap_used_mb = int(sw)
    except Exception:
        pass
    try:
        temp = _run(["bash", "-c", "sensors 2>/dev/null | grep -m1 'Package id 0' | awk '{print $4}' | tr -d '+°C'"])
        if temp and temp != "0":
            snap.cpu_temp_c = float(temp)
    except Exception:
        pass
    try:
        df = _run(["bash", "-c", "df --output=pcent / | tail -1 | tr -d '%'"])
        if df:
            snap.disk_used_pct = float(df)
    except Exception:
        pass
    try:
        gpu = _run(["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used", "--format=csv,noheader,nounits"])
        if gpu:
            parts = [p.strip() for p in gpu.split(",")]
            snap.gpu_name = parts[0]
            snap.gpu_util = int(parts[1])
            snap.gpu_mem_used_mb = int(parts[2])
    except Exception:
        pass
    return snap


def collect_aura() -> AuraSnapshot:
    snap = AuraSnapshot()
    try:
        status = json.loads((CACHE / "aura_status.json").read_text())
        snap.state = status.get("state", "unknown")
        snap.text = status.get("text", "")
    except Exception:
        pass
    for svc in ["aura.service", "aura-dbus.service", "aura-tray.service"]:
        try:
            state = _run(["systemctl", "--user", "is-active", svc])
            snap.services[svc] = state
        except Exception:
            snap.services[svc] = "unknown"
    return snap


def snapshot() -> dict:
    return {
        "resources": asdict(collect_resources()),
        "aura": asdict(collect_aura()),
        "ts": datetime.now(UTC).timestamp(),
    }


def write_state(data: dict) -> None:
    SHELL_STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = SHELL_STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    os.replace(tmp, SHELL_STATE)


async def run_loop(interval: float = 2.0) -> None:
    """Пишет shell_state.json каждые N секунд."""
    log.info("shell daemon started (interval=%.1fs)", interval)
    while True:
        try:
            data = snapshot()
            write_state(data)
        except Exception as e:
            log.warning("snapshot failed: %s", e)
        await asyncio.sleep(interval)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_loop())
