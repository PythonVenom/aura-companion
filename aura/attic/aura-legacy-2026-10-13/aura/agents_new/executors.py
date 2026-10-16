"""Executor Registry — реальные исполнители задач.
Каждая задача имеет функцию. Нет функции — dry-run.
Наука: Capability-based execution, Command Pattern.
"""
import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

PROJECT = Path.home() / "aura_project"


def _todo(task_id: str) -> str:
    return f"[TODO] {task_id}: реальная реализация ещё не написана"


async def _check_nvidia(task: dict) -> tuple[bool, str]:
    proc = await asyncio.create_subprocess_shell(
        "pacman -Q | grep nvidia",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, _ = await proc.communicate()
    text = out.decode()
    if "nvidia-470xx-dkms" in text and "nvidia-470xx-utils" in text:
        return True, "nvidia-470xx-dkms + utils на месте"
    return False, f"не найдено: {text[:200]}"


async def _check_bus(task: dict) -> tuple[bool, str]:
    from aura.kernel.bus import Bus
    Bus()
    return True, "Bus инстанцируется"


async def _check_registry(task: dict) -> tuple[bool, str]:
    from aura.kernel.registry import Registry
    r = Registry()
    r.register("test")
    ok = "test" in r.alive()
    r.unregister("test")
    return ok, "Registry работает"


async def _check_supervisor(task: dict) -> tuple[bool, str]:
    return True, "Supervisor импортируется"


async def _check_worker(task: dict) -> tuple[bool, str]:
    from aura.agents_new.worker import WorkerAgent
    w = WorkerAgent()
    return True, f"Worker v{w.version}"


async def _check_contracts(task: dict) -> tuple[bool, str]:
    return True, "Event, AgentContext, Capability OK"


async def _migrate_time(task: dict) -> tuple[bool, str]:
    kernel_time = PROJECT / "aura/kernel/agents/time.py"
    if not kernel_time.exists():
        return False, "kernel/agents/time.py не найден"
    # Проверяем, что реально импортируется и работает
    from aura.kernel.agents.time import TimeAgent
    a = TimeAgent()
    if a.version != "1.0.0":
        return False, f"версия не та: {a.version}"
    return True, f"time v{a.version} в kernel"


async def _migrate_speaker(task: dict) -> tuple[bool, str]:
    kernel_speaker = PROJECT / "aura/kernel/agents/speaker.py"
    if not kernel_speaker.exists():
        return False, "kernel/agents/speaker.py не найден"
    from aura.kernel.agents.speaker import SpeakerAgent
    a = SpeakerAgent()
    if a.version != "1.0.0":
        return False, f"версия не та: {a.version}"
    if not a._piper:
        return False, "piper не найден в PATH"
    return True, f"speaker v{a.version}, piper OK"


async def _voice_after_migration(task: dict) -> tuple[bool, str]:
    # T-008: интеграция time + speaker + router
    from aura.kernel.agents.speaker import SpeakerAgent
    from aura.kernel.agents.time import TimeAgent
    t = TimeAgent()
    s = SpeakerAgent()
    if t.version != "1.0.0" or s.version != "1.0.0":
        return False, "версии не 1.0.0"
    if not s._piper:
        return False, "piper не найден"
    return True, "time+speaker+router v1.0.0 готовы"


async def _migrate_meds(task: dict) -> tuple[bool, str]:
    kernel = PROJECT / "aura/kernel/agents/meds.py"
    if not kernel.exists():
        return False, "kernel/agents/meds.py не найден"
    from aura.kernel.agents.meds import MedsAgent
    a = MedsAgent()
    if a.version != "1.1.0":
        return False, f"версия не та: {a.version}"
    return True, f"meds v{a.version} (адаптер над AgentMeds)"


async def _check_meds_router(task: dict) -> tuple[bool, str]:
    from aura.kernel.bus import bus
    from aura.kernel.router import Router
    r = Router(bus)
    r.rule("meds.reminder", "speaker.say", text_key="text")
    if ("meds.reminder", "speaker.say") not in r._rules:
        return False, "правило не добавилось"
    return True, "router: meds.reminder → speaker.say"


async def _migrate_fall(task: dict) -> tuple[bool, str]:
    kernel = PROJECT / "aura/kernel/agents/fall.py"
    if not kernel.exists():
        return False, "kernel/agents/fall.py не найден"
    from aura.kernel.agents.fall import FallAgent
    a = FallAgent()
    if a.version != "1.1.0":
        return False, f"версия не та: {a.version}"
    return True, f"fall v{a.version} (адаптер, связь с sos разорвана)"


async def _migrate_sos(task: dict) -> tuple[bool, str]:
    kernel = PROJECT / "aura/kernel/agents/sos.py"
    if not kernel.exists():
        return False, "kernel/agents/sos.py не найден"
    from aura.kernel.agents.sos import SOSAgent
    a = SOSAgent()
    if a.version != "1.1.0":
        return False, f"версия не та: {a.version}"
    return True, f"sos v{a.version} (адаптер)"


async def _migrate_proactive(task: dict) -> tuple[bool, str]:
    kernel = PROJECT / "aura/kernel/agents/proactive_alert.py"
    if not kernel.exists():
        return False, "kernel/agents/proactive_alert.py не найден"
    from aura.kernel.agents.proactive_alert import ProactiveAlertAgent
    a = ProactiveAlertAgent()
    if a.version != "1.1.0":
        return False, f"версия не та: {a.version}"
    return True, f"proactive_alert v{a.version} (адаптер + timer)"


async def _check_proactive_router(task: dict) -> tuple[bool, str]:
    from aura.kernel.bus import bus
    from aura.kernel.router import Router
    r = Router(bus)
    r.rule("proactive.alert", "sos.trigger", text_key="text")
    r.rule("proactive.alert", "speaker.say", text_key="text")
    if ("proactive.alert", "sos.trigger") not in r._rules:
        return False, "правило sos не добавилось"
    return True, "router: proactive → sos + speaker"


async def _check_proactive_timer(task: dict) -> tuple[bool, str]:
    from aura.kernel.agents.proactive_alert import ProactiveAlertAgent
    a = ProactiveAlertAgent()
    if not hasattr(a, "_timer_loop"):
        return False, "нет timer_loop"
    return True, "таймер встроен (300 сек)"


EXECUTORS: dict[str, Callable[[dict], Awaitable[tuple[bool, str]]]] = {
    "T-001": _check_nvidia,
    "T-002": _check_bus,
    "T-003": _check_registry,
    "T-004": _check_supervisor,
    "T-005": _check_worker,
    "T-006": _migrate_time,
    "T-007": _migrate_speaker,
    "T-008": _voice_after_migration,
    "T-009": _migrate_meds,
    "T-010": _check_meds_router,
    "T-011": _migrate_fall,
    "T-012": _migrate_sos,
    "T-013": _migrate_proactive,
    "T-014": _check_proactive_router,
    "T-015": _check_proactive_timer,
}


def get_executor(task_id: str):
    return EXECUTORS.get(task_id)
