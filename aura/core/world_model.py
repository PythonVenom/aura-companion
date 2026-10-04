"""World Model — состояние системы (ADR-100)."""
from __future__ import annotations
import subprocess
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class WorldState:
    files: list = field(default_factory=list)
    windows: list = field(default_factory=list)
    tabs: list = field(default_factory=list)
    processes: list = field(default_factory=list)
    user_recent: list = field(default_factory=list)
    ts: float = field(default_factory=time.time)

    def to_dict(self):
        return asdict(self)


def scan_windows() -> list:
    try:
        r = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, timeout=2)
        out = []
        for line in r.stdout.splitlines():
            parts = line.split(None, 3)
            if len(parts) >= 4:
                out.append({"id": parts[0], "desktop": parts[1], "title": parts[3]})
        return out
    except Exception:
        return []


def scan_processes(top: int = 20) -> list:
    try:
        r = subprocess.run(
            ["ps", "-eo", "comm,%cpu", "--sort=-%cpu"],
            capture_output=True, text=True, timeout=2,
        )
        out = []
        for line in r.stdout.splitlines()[1:top+1]:
            parts = line.split()
            if len(parts) >= 2:
                out.append({"name": parts[0], "cpu": parts[1]})
        return out
    except Exception:
        return []


def scan_recent_files(minutes: int = 15) -> list:
    try:
        base = Path.home()
        r = subprocess.run(
            ["find", str(base), "-maxdepth", "3", "-type", "f",
             "-mmin", f"-{minutes}", "-not", "-path", "*/.*"],
            capture_output=True, text=True, timeout=3,
        )
        return r.stdout.strip().splitlines()[:20]
    except Exception:
        return []


class WorldModel:
    def __init__(self):
        self.state = WorldState()

    def refresh(self) -> WorldState:
        self.state = WorldState(
            windows=scan_windows(),
            processes=scan_processes(),
            files=scan_recent_files(),
        )
        return self.state

    def summary(self) -> str:
        s = self.state
        lines = [f"Окон: {len(s.windows)}", f"Процессов: {len(s.processes)}", f"Файлов (15 мин): {len(s.files)}"]
        if s.windows:
            lines.append("Топ окон:")
            for w in s.windows[:3]:
                lines.append(f"  - {w['title'][:50]}")
        return "\n".join(lines)


_world = WorldModel()


def get_world() -> WorldModel:
    return _world


__all__ = ["WorldModel", "WorldState", "get_world"]
