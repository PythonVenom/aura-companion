"""Prometheus-совместимые метрики (text exposition format).

Использование:
    python -m aura.metrics
    # Или GET /metrics через http.server
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


def collect() -> dict:
    """Собрать метрики."""
    m = {}

    # Service status
    try:
        r = subprocess.run(["systemctl", "--user", "is-active", "aura.service"],
                           capture_output=True, text=True, timeout=2)
        m["aura_service_active"] = 1 if r.stdout.strip() == "active" else 0
    except Exception:
        m["aura_service_active"] = 0

    # Calendar events today
    try:
        from aura.agents import chat_sense
        m["aura_calendar_today"] = len(chat_sense.get_today())
    except Exception:
        m["aura_calendar_today"] = 0

    # Unanswered
    try:
        from aura.agents import chat_sense
        from aura.agents.messenger import send_command
        r = send_command({"action": "max_list_chats"})
        previews = r.get("data", {}).get("chats", []) if r else []
        m["aura_unanswered_count"] = len(chat_sense.find_unanswered(previews))
    except Exception:
        m["aura_unanswered_count"] = 0

    # FSM state (numeric)
    try:
        fsm = Path(str(Path.home() / ".cache/aura/fsm.json"))
        if fsm.exists():
            state = json.loads(fsm.read_text()).get("state", "idle")
            m["aura_fsm_idle"] = 1 if state == "idle" else 0
        else:
            m["aura_fsm_idle"] = 1
    except Exception:
        m["aura_fsm_idle"] = 0

    return m


def format_prometheus(m: dict) -> str:
    """Text exposition format."""
    lines = []
    for k, v in m.items():
        lines.append(f"# TYPE {k} gauge")
        lines.append(f"{k} {v}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(format_prometheus(collect()))
