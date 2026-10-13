"""Aura Studio — визуальный секвенсор-кабинет.

Дорожки:
  🎤 Голос, 🧠 LLM, 🎵 Музыка, 🩺 Meds, 🚨 SOS, 💬 VK, 🔌 PC

Плейлист:
  Утро, Работа, Обед, Вечер — что когда

События:
  Лог последних 10 событий

Наука: Csikszentmihalyi 1990 (flow через обзор),
       Nielsen 1993 (visibility of system status).
"""
from __future__ import annotations

import contextlib
import subprocess
from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Label

REPO = Path("/home/pythonvenom/aura-companion")


# ─── Модель ────────────────────────────────────────────

TRACKS = [
    ("🎤 Голос",   "voice"),
    ("🧠 LLM",     "llm"),
    ("🎵 Музыка",  "music"),
    ("🩺 Meds",    "meds"),
    ("🚨 SOS",     "sos"),
    ("💬 VK",      "vk"),
    ("🔌 PC",      "pc"),
]


def detect_track_states() -> dict[str, bool]:
    """Кто из агентов сейчас активен."""
    states = {k: False for _, k in TRACKS}

    # Голос
    with contextlib.suppress(Exception):
        r = subprocess.run(
            ["pgrep", "-f", "piper"], capture_output=True, timeout=2,
        )
        states["voice"] = r.returncode == 0

    # LLM
    with contextlib.suppress(Exception):
        r = subprocess.run(
            ["pgrep", "-f", "ollama"], capture_output=True, timeout=2,
        )
        states["llm"] = r.returncode == 0

    # Музыка
    with contextlib.suppress(Exception):
        r = subprocess.run(
            ["pgrep", "-f", "mpv"], capture_output=True, timeout=2,
        )
        states["music"] = r.returncode == 0

    # Демон
    with contextlib.suppress(Exception):
        r = subprocess.run(
            ["systemctl", "--user", "is-active", "aura.service"],
            capture_output=True, text=True, timeout=2,
        )
        daemon_active = r.stdout.strip() == "active"
        states["meds"] = daemon_active
        states["sos"] = daemon_active

    # Bridge
    with contextlib.suppress(Exception):
        states["vk"] = Path("/tmp/aura_firefox.sock").exists()

    # PC
    states["pc"] = True

    return states


def track_bar(active: bool, width: int = 40) -> str:
    """Полоска активности."""
    if active:
        # Живой поток
        return "▓▓▓░░▓▓▓▓░░░▓▓▓░░▓▓▓▓░░░▓▓▓░░▓▓▓▓░"
    return "░" * width


def current_state() -> dict:
    """Состояние корабля."""
    state = {
        "xp": 0, "rank": "?", "sector": "?", "progress": 0.0,
    }
    with contextlib.suppress(Exception):
        from aura.game.state import StateStore
        from aura.profiles import get_profile
        profile = get_profile()
        s = StateStore(db_path=str(profile.state_db),
                       key=profile.path.joinpath("db.key").read_text().strip()
                       if profile.path.joinpath("db.key").exists() else None)
        st = s.load()
        state["xp"] = st.xp
        state["rank"] = st.rank
        state["sector"] = st.sector
        state["progress"] = getattr(st, "progress", 0.0)
        s.close()
    return state


# ─── Приложение ────────────────────────────────────────

class AuraStudio(App):
    """Секвенсор-кабинет Aura."""

    CSS = """
    Screen { background: $surface; }
    #tracks { height: auto; padding: 1; }
    #playlist { height: auto; padding: 1; }
    #events { height: auto; padding: 1; }
    .track { padding: 0 1; }
    .active { color: $success; }
    .inactive { color: $text-disabled; }
    """

    BINDINGS = [
        ("q", "quit", "Выход"),
        ("r", "refresh", "Обновить"),
        ("s", "status", "Статус"),
        ("d", "doctor", "Доктор"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="tracks"):
            yield Label("─── ДОРОЖКИ ───────────────────────────────")
            for _label, _key in TRACKS:
                yield Label("", id=f"track_{_key}", classes="track")
        with Container(id="playlist"):
            yield Label("─── ПЛЕЙЛИСТ ──────────────────────────────")
            yield Label("[1] 🌅 Утро   07:00  greeting + план")
            yield Label("[2] 💼 Работа 09:00  focus mode")
            yield Label("[3] 🍱 Обед   13:00  напоминание")
            yield Label("[4] 🌆 Вечер  18:00  музыка + отдых")
        with Container(id="events"):
            yield Label("─── СОБЫТИЯ ──────────────────────────────")
            yield Label("", id="events_log")
        yield Footer()

    def on_mount(self) -> None:
        self.action_refresh()
        self.set_interval(2.0, self.action_refresh)

    def action_refresh(self) -> None:
        """Обновить все данные."""
        # Состояние
        st = current_state()
        self.title = "🛸 AURA STUDIO"
        self.sub_title = (
            f"Сектор: {st['sector']}  ·  "
            f"XP {st['xp']}  ·  {st['rank']}  ·  "
            f"Сборка {st['progress']}%"
        )

        # Дорожки
        states = detect_track_states()
        for label, key in TRACKS:
            widget = self.query_one(f"#track_{key}", Label)
            active = states.get(key, False)
            mark = "●" if active else "○"
            bar = track_bar(active)
            widget.update(f"{label:<10} [{mark}]  {bar}")
            widget.set_classes("track active" if active else "track inactive")

        # События
        log_path = Path("/tmp/aura_post_commit.log")
        events_text = ""
        if log_path.exists():
            with contextlib.suppress(Exception):
                lines = log_path.read_text().splitlines()[-5:]
                events_text = "\n".join(lines)
        if not events_text:
            events_text = f"{datetime.now().strftime('%H:%M')}  (журнал пуст)"
        with contextlib.suppress(Exception):
            self.query_one("#events_log", Label).update(events_text)

    def action_status(self) -> None:
        """aurа status."""
        self.exit()
        subprocess.run([str(REPO / "venv" / "bin" / "python"),
                        "scripts/aura.py", "status"])

    def action_doctor(self) -> None:
        """aura doctor."""
        self.exit()
        subprocess.run([str(REPO / "venv" / "bin" / "python"),
                        "scripts/aura.py", "doctor"])


def run_studio() -> None:
    """Запустить студию."""
    app = AuraStudio()
    app.run()


__all__ = ["AuraStudio", "run_studio"]


if __name__ == "__main__":
    run_studio()
