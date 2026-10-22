#!/usr/bin/env bash
# Live-тест голосом: Bug E (числа-слова) + Bug F (Тест/тс)
# Использование: scripts/live_voice_test.sh [log_path]
set -euo pipefail
cd "$(dirname "$0")/.."
LOG="${1:-/tmp/aura_live_voice.log}"
exec > >(tee -a "$LOG") 2>&1

echo "[$(date -Iseconds)] live_voice_test start"

python3 << 'PY'
import asyncio
from aura.agents.time_agent import AgentTimeAgent
from aura.agents.massage import AgentMassage
from aura.core.protocol import AgentRequest

CASES = [
    ("time",    "таймер тридцать секунд", "30"),
    ("time",    "таймер 30 секунд",       "30"),
    ("massage", "сессия Тест 30",         "Тест"),
    ("massage", "сессия тс 30",           "Тест"),
]

async def run():
    ta, ma = AgentTimeAgent(), AgentMassage()
    ok = True
    for kind, text, needle in CASES:
        agent = ta if kind == "time" else ma
        r = await agent.handle(AgentRequest(text=text))
        got = (r.text or "")
        good = needle.lower() in got.lower()
        ok = ok and good
        print(f"[{'PASS' if good else 'FAIL'}] {kind:8} {text!r} -> {got!r}")
    return 0 if ok else 1

raise SystemExit(asyncio.run(run()))
PY
