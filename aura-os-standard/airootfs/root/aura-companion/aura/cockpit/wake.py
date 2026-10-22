"""Wake — пробуждение корабля.

Один вызов делает всё:
1. Музыка под событие (mpv)
2. Голос Ауры (Piper)
3. Запись в бортовой журнал
4. Обновление GameState
5. Приветствие по времени суток, если давно не виделись

Наука: Licklider 1960 (симбиоз), Duhigg 2012 (habit loop).
"""

from __future__ import annotations

from datetime import UTC, datetime
from datetime import datetime as _dt

from aura.cockpit.hyperjump import current_commit, did_hyperjump, hyperjump_context
from aura.cockpit.music import Music, track_for_event
from aura.cockpit.scheduler import greeting_context, greeting_event, should_greet
from aura.game.state import StateStore
from aura.lore.persona import speak_line
from aura.lore.story import StoryLog
from aura.voice.orchestrator import VoiceOrchestrator


def _play_music(event: str) -> None:
    track = track_for_event(event)
    if track:
        Music.instance().play(track)


def wake() -> str:
    """Утренний / вечерний брифинг. Возвращает фразу для печати."""
    store = StateStore()
    state = store.load()
    story = StoryLog()
    now = datetime.now(UTC)
    local_now = _dt.now()   # для приветствия — локальное время

    # 1. Гиперпрыжок? (сменился ли commit)
    if did_hyperjump(state.last_commit, None):
        _play_music("hyperjump")
        ctx = hyperjump_context(state)
        VoiceOrchestrator().say("hyperjump", **ctx)

    # 2. Приветствие по времени (если давно не виделись)
    line = ""
    event = greeting_event(local_now.hour)
    if should_greet(state.last_seen, now=now):
        _play_music(event)
        ctx = greeting_context(state, story)
        line = speak_line(event, **ctx)
        VoiceOrchestrator().say(event, **ctx)

    # 3. Обновить last_seen
    state.last_seen = now.isoformat()
    state.last_commit = current_commit()
    store.save(state)
    store.close()

    print(f"📋 {line}")
    return line


if __name__ == "__main__":
    wake()
