"""
Агент паузы медиа (AgentMediaPause).

На время речи Ауры — пауза MPRIS-плееров. Возобновляем ТОЛЬКО тех,
кого паузили. Иначе resume включает всех — двойной звук.

Почему пауза, а не ducking:
- Firefox на PipeWire пересоздаёт audio-stream при per-stream volume —
  pactl set-sink-input-volume не срабатывает.
- MPRIS работает везде: Firefox, VLC, mpv, Spotify.
- Для UX беты пауза лучше ducking: полная тишина → Аура слышна чётко.

По науке:
- Изолирован (subprocess + playerctl)
- Тестируем (mock subprocess, живой звук НЕ трогаем)
- Best-effort: ошибки глотаются, плеер без MPRIS игнорируется

См. ADR-006, ADR-008.
"""

from __future__ import annotations

import shutil
import subprocess

from aura.agents import media_state
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent
from aura.platform import get_media


class AgentMediaPause(BaseAgent):
    """
    Пауза MPRIS-плееров на время речи.

    Публичные методы:
    - pause(): пауза всех играющих, помним кого. True если хоть кого-то.
    - resume(): возобновление только паузившихся. True если хоть кого-то.
    """

    name = "media_pause"
    MODULE_ALWAYS = True

    KEYWORDS = (
        "поставь на паузу",
        "возобнови музыку",
        "продолжи музыку",
        "сними с паузы",
        "пауза",
        "продолжи",
        "возобнови",
        "стоп музыка",
        "останови музыку",
    )

    def __init__(self, player: str | None = None) -> None:
        super().__init__()
        self.player = player  # None = все MPRIS-плееры; иначе конкретный
        self.ready = shutil.which("playerctl") is not None
        self._paused_players: list[str] = []  # кого мы паузили

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        if not any(kw in text for kw in self.KEYWORDS):
            return False
        # Bug 14 ph.3: только если last_active=vk или mpris.
        # Если local — music_local обработает первым.
        return media_state.get_active() in ("vk", "mpris")

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()
        if any(kw in text for kw in ("возобнови музыку", "продолжи музыку", "сними с паузы")):
            ok = self.resume()
            return AgentResponse.ok("▶️ Музыка продолжена" if ok else "▶️ Нечего возобновлять", self.name)
        if "пауза" in text or "поставь" in text:
            ok = self.pause()
            return AgentResponse.ok("⏸️ Музыка на паузе" if ok else "⏸️ Нечего ставить на паузу", self.name)
        return AgentResponse.not_handled(self.name)

    # --- Публичные методы ---

    def pause(self) -> bool:
        """Пауза. ADR-017: через PAL, fallback на playerctl."""
        try:
            ok = get_media().pause_all()
            if ok:
                return True
        except Exception as e:
            # F-006: не глотать (раздел 17 промта)
            import logging
            logging.getLogger('aura.media_pause').debug(
                'media_pause error: %s', e)
        if not self.ready:
            return False
        players = [self.player] if self.player else self._list_players()
        paused: list[str] = []
        for p in players:
            if self._player_status(p) == "Playing" and self._player_cmd(p, "pause"):
                paused.append(p)
        if paused:
            self._paused_players = paused
            from aura.agents import media_state
            media_state.set_active("mpris")
            return True
        return False

    def resume(self) -> bool:
        """Возобновление только тех, кого паузили."""
        if not self.ready or not self._paused_players:
            return False
        ok = False
        for p in self._paused_players:
            if self._player_cmd(p, "play"):
                ok = True
        self._paused_players = []
        return ok

    # --- Внутренние ---

    def _list_players(self) -> list[str]:
        """Список имён MPRIS-плееров."""
        try:
            r = subprocess.run(
                ["playerctl", "--list-all"],
                capture_output=True, text=True, timeout=2,
            )
            return [line.strip() for line in r.stdout.splitlines() if line.strip()]
        except Exception:
            return []

    def _player_status(self, name: str) -> str:
        """Статус конкретного плеера: Playing / Paused / Stopped. '' при ошибке."""
        try:
            r = subprocess.run(
                ["playerctl", "-p", name, "status"],
                capture_output=True, text=True, timeout=2,
            )
            return r.stdout.strip()
        except Exception:
            return ""

    def _player_cmd(self, name: str, action: str) -> bool:
        try:
            r = subprocess.run(
                ["playerctl", "-p", name, action],
                capture_output=True, text=True, timeout=2,
            )
            return r.returncode == 0
        except Exception:
            return False


__all__ = ["AgentMediaPause"]
