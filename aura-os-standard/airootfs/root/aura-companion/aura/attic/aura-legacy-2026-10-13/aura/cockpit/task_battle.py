"""F-101b: TaskBattleScreen — бой за задачу сектора.

Задачи из campaign.py — не ruff-ошибки, а реальные фичи (CI, make doctor).
Каждая задача = один Problem. Победа → state.quests_done.append(id).
"""
from __future__ import annotations

import contextlib

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Log, Static

from aura.game.state import StateStore
from aura.lore.campaign import SECTORS, open_tasks


class TaskBattleScreen(ModalScreen):
    """Бой за задачи сектора."""

    CSS = """
    TaskBattleScreen { align: center middle; }
    #tb-box {
        width: 90%;
        height: 85%;
        border: thick #ff6666;
        background: #1a0008;
        padding: 1 2;
    }
    #tb-title { text-style: bold; color: #ff8888; padding: 0 0 1 0; }
    #tb-hud { height: 4; padding: 0 0 1 0; }
    #tb-tasks { height: 1fr; border: solid #444444; padding: 1; }
    #tb-log { height: 8; border: solid #444444; margin: 1 0; }
    #tb-actions { height: 3; }
    #tb-actions Button { margin: 0 1; }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Выход [Esc]"),
        Binding("a", "attack_all", "Атаковать [a]"),
        Binding("r", "refresh", "Обновить [r]"),
    ]

    def __init__(self, sector: str) -> None:
        super().__init__()
        self.sector = sector
        self._log_lines: list[str] = []

    def compose(self) -> ComposeResult:
        with Container(id="tb-box"):
            yield Static(f"⚔ БОЙ ЗА СЕКТОР {self.sector}", id="tb-title")
            yield Static("", id="tb-hud")
            with Vertical(id="tb-tasks"):
                yield Static("", id="tb-tasks-inner")
            yield Log(id="tb-log")
            with Horizontal(id="tb-actions"):
                yield Button("⚔ Атаковать все [a]", id="btn-attack",
                             variant="error")
                yield Button("Закрыть [Esc]", id="btn-close",
                             variant="primary")

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        """Обновить HUD и список задач."""
        # F-101c: проверка attackable
        sector_meta = SECTORS.get(self.sector, {})
        if not sector_meta.get("attackable", True):
            self._log("HORIZON: сектор не решается боем. Только реальная работа.")
            return
        tasks = open_tasks(self.sector)
        total = len(SECTORS.get(self.sector, {}).get("tasks", []))
        closed = total - len(tasks)

        # HUD
        hud = (
            f"📊 Прогресс: {closed}/{total} задач закрыто\n"
            f"⚔ Осталось: {len(tasks)} незакрытых"
        )
        with contextlib.suppress(Exception):
            self.query_one("#tb-hud", Static).update(hud)

        # Список задач
        lines = ["📋 Незакрытые задачи:"]
        if not tasks:
            lines.append("  ✅ Все задачи закрыты!")
        for t in tasks:
            lines.append(f"  ⬜ {t['id']:8} — {t['title']}")
        with contextlib.suppress(Exception):
            self.query_one("#tb-tasks-inner", Static).update("\n".join(lines))

    def _log(self, msg: str) -> None:
        with contextlib.suppress(Exception):
            self.query_one("#tb-log", Log).write_line(msg)

    def action_refresh(self) -> None:
        self._refresh()

    def action_attack_all(self) -> None:
        """Атака всех задач по очереди."""
        sector_meta = SECTORS.get(self.sector, {})
        if not sector_meta.get("attackable", True):
            self._log("HORIZON: этот сектор нельзя закрыть боем.")
            return
        tasks = open_tasks(self.sector)
        if not tasks:
            self._log("✅ Нет задач для атаки.")
            return

        from aura.game.problem import Problem

        killed = 0
        for t in tasks:
            self._log(f"⚔ Бой за {t['id']}: {t['title']}")
            problem = Problem(
                code=t["id"],
                sector=f"aura/tasks/{self.sector.lower()}",
                line=0,
                raw_message=t["title"],
            )
            # Применяем стратегию паттерна (по умолчанию — patch)
            strategy = problem.pattern.strategy
            try:
                ok, msg = problem.try_solve(strategy)
                if ok:
                    killed += 1
                    self._log(f"  ✅ {msg}")
                    self._mark_task_done(t["id"])
                else:
                    self._log(f"  ⚠️ {msg}")
            except Exception as e:
                self._log(f"  ❌ {e}")

        if killed:
            try:
                store = StateStore()
                st = store.load()
                st.add_xp(killed * 50)
                st.recalc_progress()
                store.save(st)
                store.close()
                self._log(f"🎉 Закрыто задач: {killed}. XP +{killed * 50}")
            except Exception as e:
                self._log(f"⚠️ State: {e}")

        self._refresh()

    def _mark_task_done(self, task_id: str) -> None:
        """Записать task_id в state.quests_done."""
        with contextlib.suppress(Exception):
            store = StateStore()
            st = store.load()
            if task_id not in st.quests_done:
                st.quests_done.append(task_id)
            store.save(st)
            store.close()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-attack":
            self.action_attack_all()
        else:
            self.dismiss(None)
