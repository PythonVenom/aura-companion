"""
Агент локальной музыки (AgentMusicLocal).

Сканирует ~/Музыка/**, играет через VLC, управляет через playerctl (MPRIS).

Команды:
- «включи музыку»          → random трек
- «включи трек X» / «включи X»  → fuzzy поиск по имени файла
- «следующий трек»         → next
- «предыдущий трек»        → previous
- «пауза»                  → pause
- «продолжи»               → play
- «стоп музыку»            → stop
- «какие треки» / «сколько треков» → список/счёт

По науке:
- Изолирован (subprocess)
- Тестируем (mock subprocess)
- Не знает про AuraCore
"""

from __future__ import annotations

import random
import subprocess
from difflib import get_close_matches
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


MUSIC_DIR = Path.home() / "Музыка"
AUDIO_EXTS = (".mp3", ".flac", ".wav", ".ogg", ".m4a", ".opus", ".wma")


class AgentMusicLocal(BaseAgent):
    """Локальная музыка из ~/Музыка."""

    name = "music_local"

    PLAY_KEYWORDS = (
        "включи музыку",
        "включи трек",
        "запусти музыку",
        "поставь музыку",
        "включи песню",
    )
    NEXT_KEYWORDS = ("следующий трек", "следующая песня", "следующий", "дальше")
    PREV_KEYWORDS = ("предыдущий трек", "предыдущая песня", "предыдущий", "назад трек")
    PAUSE_KEYWORDS = ("пауза", "поставь на паузу", "приостанови")
    RESUME_KEYWORDS = ("продолжи музыку", "включи заново", "продолжи трек",
                       "продолжи", "продолжим", "продолжите",
                       "играй", "запусти музыку заново", "включи снова")
    STOP_KEYWORDS = ("стоп музык", "останови музык", "выключи музык", "стоп музыка")
    LIST_KEYWORDS = ("какие треки", "список треков", "сколько треков")

    def __init__(self, music_dir: Path | None = None) -> None:
        super().__init__()
        self.music_dir = music_dir or MUSIC_DIR
        self.tracks: list[Path] = []
        self._last_track: Path | None = None
        self._scan()

    def _scan(self) -> None:
        """Собрать все аудиофайлы из music_dir рекурсивно."""
        self.tracks = []
        if not self.music_dir.exists():
            return
        try:
            for p in self.music_dir.rglob("*"):
                if p.is_file() and p.suffix.lower() in AUDIO_EXTS:
                    self.tracks.append(p)
        except Exception:
            pass

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        # Bug 14 ph.3: если last_active=vk — уступаем media_pause / vk_music.
        from aura.agents import media_state
        _yield_kw = (
            self.PAUSE_KEYWORDS + self.RESUME_KEYWORDS
            + self.NEXT_KEYWORDS + self.PREV_KEYWORDS + self.STOP_KEYWORDS
        )
        if media_state.get_active() == "vk" and any(kw in text for kw in _yield_kw):
            return False
        # Pause — только если VLC играет.
        if any(kw in text for kw in self.PAUSE_KEYWORDS):
            return self._vlc_playing()
        # Resume — если paused, ИЛИ если есть последний трек (после стопа).
        if any(kw in text for kw in self.RESUME_KEYWORDS):
            return self._vlc_paused() or self._last_track is not None
        # Next/prev/stop — если VLC активен в любом виде.
        if any(kw in text for kw in self.NEXT_KEYWORDS + self.PREV_KEYWORDS + self.STOP_KEYWORDS):
            return self._vlc_active()
        all_kw = (
            self.PLAY_KEYWORDS + self.LIST_KEYWORDS
        )
        if not any(kw in text for kw in all_kw):
            return False
        # Bug 14 ph.2: уступаем vk_music, если last_active=vk.
        from aura.agents import media_state
        if media_state.get_active() == "vk":
            ambiguous = ("включи музыку", "запусти музыку", "поставь музыку", "включи песню")
            # Явные VK-команды («включи вк») не наша тема — тоже уступаем.
            padded = f" {text.replace(',', ' ')} "
            is_explicit_vk = any(kw in padded for kw in (" вк ", " вконтакте ", " vk "))
            if any(kw in text for kw in ambiguous) or is_explicit_vk:
                return False
        return True

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        if any(kw in text for kw in self.LIST_KEYWORDS):
            return AgentResponse.ok(self.list_tracks(), self.name)

        if any(kw in text for kw in self.STOP_KEYWORDS):
            return AgentResponse.ok(self.stop(), self.name)

        if any(kw in text for kw in self.PAUSE_KEYWORDS):
            return AgentResponse.ok(self.pause(), self.name)

        if any(kw in text for kw in self.RESUME_KEYWORDS):
            return AgentResponse.ok(self.resume(), self.name)

        if any(kw in text for kw in self.NEXT_KEYWORDS):
            return AgentResponse.ok(self.next_track(), self.name)

        if any(kw in text for kw in self.PREV_KEYWORDS):
            return AgentResponse.ok(self.prev_track(), self.name)

        if any(kw in text for kw in self.PLAY_KEYWORDS):
            query = self._extract_query(text)
            if query:
                return AgentResponse.ok(self.play_by_query(query), self.name)
            return AgentResponse.ok(self.play_random(), self.name)

        return AgentResponse.not_handled(self.name)

    # --- Команды ---

    def play_random(self) -> str:
        if not self.tracks:
            return "🎵 Папка ~/Музыка пуста"
        track = random.choice(self.tracks)
        return self._launch(track)

    def play_by_query(self, query: str) -> str:
        if not self.tracks:
            return "🎵 Папка ~/Музыка пуста"
        names = {t: t.stem.lower() for t in self.tracks}
        q = query.lower().strip()
        # Точное вхождение
        matches = [t for t, name in names.items() if q in name]
        if not matches:
            # Fuzzy
            close = get_close_matches(q, list(names.values()), n=1, cutoff=0.6)
            if close:
                matches = [t for t, name in names.items() if name == close[0]]
        if not matches:
            return f"🎵 Трек «{query}» не найден"
        return self._launch(matches[0])

    def pause(self) -> str:
        # ADR-017: через PAL
        try:
            get_media().pause_all()
            return "⏸️ Пауза"
        except Exception:
            return self._playerctl("pause", "⏸️ Пауза")

    def resume(self) -> str:
        if self._vlc_paused():
            try:
                get_media().resume_all()
                return "▶️ Продолжаю"
            except Exception:
                return self._playerctl("play", "▶️ Продолжаю")
        # После стопа — запустить последний трек заново.
        if self._last_track is not None and self._last_track.exists():
            return self._launch(self._last_track)
        return "🎵 Нет трека для продолжения"

    def next_track(self) -> str:
        return self._playerctl("next", "⏭️ Следующий трек")

    def prev_track(self) -> str:
        return self._playerctl("previous", "⏮️ Предыдущий трек")

    def stop(self) -> str:
        return self._playerctl("stop", "⏹️ Музыка остановлена")

    def list_tracks(self) -> str:
        if not self.tracks:
            return "🎵 Папка ~/Музыка пуста"
        n = len(self.tracks)
        sample = [t.stem for t in self.tracks[:5]]
        return f"🎵 Треков: {n}\n" + "\n".join(f"  • {s}" for s in sample)

    # --- Внутренние ---

    def _launch(self, track: Path) -> str:
        from aura.agents import media_state
        media_state.set_active("local")
        try:
            subprocess.Popen(
                ["vlc", "--one-instance", str(track)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._last_track = track
            return f"🎵 Включила: {track.stem}"
        except Exception as e:
            return f"🎵 Не удалось включить: {e}"

    def _playerctl(self, action: str, ok_text: str) -> str:
        try:
            r = subprocess.run(
                ["playerctl", "-p", "vlc", action],
                capture_output=True, text=True, timeout=3,
            )
            if r.returncode == 0:
                return ok_text
            return f"🎵 VLC не отвечает ({action})"
        except Exception:
            return f"🎵 Ошибка playerctl ({action})"

    def _vlc_status(self) -> str:
        """Возвращает статус VLC: Playing / Paused / Stopped / пусто."""
        try:
            r = subprocess.run(
                ["playerctl", "-p", "vlc", "status"],
                capture_output=True, text=True, timeout=2,
            )
            return r.stdout.strip()
        except Exception:
            return ""

    def _vlc_active(self) -> bool:
        """VLC играет или на паузе."""
        return self._vlc_status() in ("Playing", "Paused")

    def _vlc_playing(self) -> bool:
        return self._vlc_status() == "Playing"

    def _vlc_paused(self) -> bool:
        return self._vlc_status() == "Paused"

    @staticmethod
    def _extract_query(text: str) -> str:
        """Извлечь «X» из «включи трек X» / «включи X»."""
        for kw in ("включи трек ", "включи песню ", "включи музыку "):
            if kw in text:
                rest = text[text.index(kw) + len(kw):].strip(".,!? ")
                # «включи музыку» без ничего → random
                if not rest or rest == "музыку":
                    return ""
                return rest
        return ""


__all__ = ["AgentMusicLocal", "MUSIC_DIR", "AUDIO_EXTS"]
