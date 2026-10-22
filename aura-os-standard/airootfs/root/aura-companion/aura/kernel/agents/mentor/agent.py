"""Mentor Agent ??? ?????????????????? ?????????????????? ?? Skill Graph.
??????????: Voice UI (Pieraccini 2012), Octalysis, FSRS.
"""
import logging

from aura.contracts.agent import AgentContext, Event
from aura.kernel.agents.mentor.ledger import ProfileLedger
from aura.kernel.agents.mentor.path import PathTracker
from aura.kernel.agents.mentor.ui import render_menu
from aura.kernel.log import event_log
from aura.kernel.payload import get_payload

log = logging.getLogger("aura.agents.mentor")


class MentorAgent:
    name = "mentor"
    version = "1.0.0"

    def __init__(self, user: str = "batya"):
        self.ctx: AgentContext | None = None
        self._running = False
        self.user = user
        self.tracker = None
        self.ledger = None

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        self.tracker = PathTracker(self.user)  # type: ignore[assignment]
        self.ledger = ProfileLedger(self.user)  # type: ignore[assignment]
        ctx.bus.subscribe("mentor.next", self._on_next)
        ctx.bus.subscribe("mentor.stats", self._on_stats)
        ctx.bus.subscribe("mentor.complete", self._on_complete)
        log.info("mentor started (user=%s)", self.user)
        event_log.append("agent.started",
                         {"name": self.name, "v": self.version,
                          "user": self.user},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _on_next(self, event) -> None:
        task = self.tracker.next_task()  # type: ignore[attr-defined]
        if not task:
            text = "?????? ?????????????????? ???????????? ????????????????. ???? ??????????????, ????????!"
        else:
            text = f"?????????????????? ??????: {task.name}. ?????????????? {task.level}. ?????????? {task.duration_h:.0f} ??????????."
        event_log.append("mentor.next",
                         {"task": task.id if task else None},
                         src=self.name)
        if self.ctx:
            event_log.append("mentor.answer", {"text": text[:80]}, src=self.name)  # AURA_MENTOR_LOG_V1
            await self.ctx.bus.publish("mentor.answer", {"text": text})

    async def _on_stats(self, event) -> None:
        s = self.tracker.stats()  # type: ignore[attr-defined]
        render_menu(self.tracker)  # type: ignore[arg-type]
        c = self.ledger.career_score()  # type: ignore[attr-defined]
        text = (f"????????????????: {s['done']} ???? {s['total']} ({s['percent']}%). "
                f"??????????????: {c['career_score']}.")
        event_log.append("mentor.stats", s, src=self.name)
        if self.ctx:
            event_log.append("mentor.answer", {"text": text[:80]}, src=self.name)  # AURA_MENTOR_LOG_V1
            await self.ctx.bus.publish("mentor.answer", {"text": text})  # type: ignore[attr-defined]

    async def _on_complete(self, event) -> None:
        p = get_payload(event)
        skill_id = p.get("skill_id")
        score = int(p.get("score", 80))
        if not skill_id:
            return
        opened = self.tracker.complete(skill_id, score)  # type: ignore[attr-defined]
        self.ledger.add(skill_id, score, reviewer="aura")  # type: ignore[attr-defined]
        text = f"?????????? {skill_id} ????????????. ??????????????: {len(opened)} ??????????."
        event_log.append("mentor.completed",
                         {"skill": skill_id, "score": score,
                          "opened": opened}, src=self.name)
        if self.ctx:
            event_log.append("mentor.answer", {"text": text[:80]}, src=self.name)  # AURA_MENTOR_LOG_V1
            await self.ctx.bus.publish("mentor.answer", {"text": text})

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "version": self.version,
                "user": self.user}

    async def stop(self) -> None:
        self._running = False
        if self.ctx:
            for t in ("mentor.next", "mentor.stats", "mentor.complete"):
                for h in list(self.ctx.bus._subs.get(t, [])):
                    self.ctx.bus.unsubscribe(t, h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
