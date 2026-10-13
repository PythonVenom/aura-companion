"""F-091b: BattleScreen на engine.py.

Интеграция с существующим движком:
- spawn_enemies_from_ruff → враги из реальных багов
- resolve_combat → формулы боя
- GameEngine.Phase → фазы
- GameState.add_xp → прогресс
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Log, Static

from aura.game.engine import GameEngine
from aura.game.spawner import spawn_enemies_from_ruff
from aura.game.state import StateStore
from aura.lore.advisors import ADVISORS, advisor_speak


class BattleScreen(ModalScreen):
    """Экран боя (F-091b). Работает через GameEngine."""

    CSS = """
    BattleScreen { align: center middle; }
    #battle-box {
        width: 85%;
        height: 75%;
        border: thick #ff4444;
        background: #1a0008;
        padding: 1 2;
    }
    #battle-title { text-style: bold; color: #ff6666; padding: 0 0 1 0; }
    #battle-hud { height: 8; padding: 0 0 1 0; }
    #battle-log { height: 1fr; border: solid #444444; margin: 1 0; }
    #battle-actions { height: 3; }
    #battle-actions Button { margin: 0 1; }
    """

    BINDINGS = [
        Binding("a", "attack", "Атака [a]"),
        Binding("r", "rewrite", "Ракета [r]"),
        Binding("d", "debug", "Дрон [d]"),
        Binding("f", "autofix", "Импульс [f]"),
        Binding("s", "skip", "Прыжок [s]"),
        Binding("c", "counsel", "Советник [c]"),
        Binding("escape", "flee", "Бежать [Esc]"),
    ]

    def __init__(self, sector: str) -> None:
        super().__init__()
        self.sector = sector

        # State
        self.store = StateStore()
        self.state = self.store.load()

        # Враги из ruff-ошибок
        try:
            self._all_enemies = spawn_enemies_from_ruff("aura/")
        except Exception:
            self._all_enemies = []

        # Engine
        self.engine = GameEngine(state=self.state)
        self.engine.scan(self._all_enemies)

    # ── UI ──────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        with Container(id="battle-box"):
            yield Static(f"⚔  БОЙ · {self.sector}", id="battle-title")
            yield Static(self._hud_text(), id="battle-hud")
            yield Log(id="battle-log")
            with Horizontal(id="battle-actions"):
                yield Button("Атака [a]", id="btn-attack", variant="error")
                yield Button("Ракета [r]", id="btn-rewrite", variant="error")
                yield Button("Прыжок [s]", id="btn-skip", variant="warning")
                yield Button("Бежать [Esc]", id="btn-flee")

    def on_mount(self) -> None:
        n = len(self._all_enemies)
        if n == 0:
            self._log("✅ Сектор чист. Врагов нет.")
        else:
            self._log(f"⚔ Найдено врагов: {n}")
            self._show_current()

    def _show_current(self) -> None:
        e = self.engine.current_enemy
        if e:
            self._log(f"🎯 Цель: {e.name} [{e.enemy_type}] HP {e.hp}")

    def _hud_text(self) -> str:
        e = self.engine.current_enemy
        enemy_line = "(нет цели)"
        if e:
            enemy_line = f"{e.name} [{e.enemy_type}] HP {e.hp}"
        ph = "█" * max(0, self.state.hull // 10) + "░" * max(0, 10 - self.state.hull // 10)
        sh = "█" * max(0, self.state.shields // 10) + "░" * max(0, 10 - self.state.shields // 10)
        return (
            f"👤 {self.state.rank:10} XP {self.state.xp:5}  Lvl {self.state.level}\n"
            f"🛡 Корпус: {ph} {self.state.hull}%\n"
            f"⚡ Щиты:  {sh} {self.state.shields}%\n"
            f"🎯 {enemy_line}\n"
            f"📦 Фаза: {self.engine.phase}"
        )

    def _refresh_hud(self) -> None:
        self.query_one("#battle-hud", Static).update(self._hud_text())

    def _log(self, msg: str) -> None:
        self.query_one("#battle-log", Log).write_line(msg)

    # ── действия ────────────────────────────────────────
    def _do_action(self, action: str) -> None:
        if self.engine.current_enemy is None:
            self._log("Нет цели.")
            return

        rd = self.engine.choose_weapon(action)
        for line in rd.lines:
            self._log(line)
        self._refresh_hud()

        # После результата — если враг убит, следующая цель
        if self.engine.last_result is not None:
            res = self.engine.last_result
            if getattr(res, "enemy_destroyed", False):
                nxt = self.engine.next_target()
                for line in nxt.lines:
                    self._log(line)
                self._show_current()
                self._refresh_hud()

    def action_counsel(self) -> None:
        """c — советник говорит про бой."""
        import random
        key = random.choice(["tactician", "engineer", "navigator"])
        adv = ADVISORS[key]
        context = "battle_start" if self.engine.current_enemy else "sector_clean"
        line = advisor_speak(key, context) or adv.motto
        self._log(f"{adv.emoji} {adv.name}: {line}")
        try:
            from aura.voice.orchestrator import get_voice
            get_voice().say_text(f"{adv.name}. {line}")
        except Exception:
            pass

    def action_attack(self) -> None:
        self._do_action("fix_anchor")

    def action_rewrite(self) -> None:
        self._do_action("rewrite")

    def action_debug(self) -> None:
        self._do_action("debug")

    def action_autofix(self) -> None:
        self._do_action("autofix")

    def action_skip(self) -> None:
        self._do_action("skip")
        self._log("Esc — завершить бой")

    def action_flee(self) -> None:
        self._save_and_close(won=False)

    def _save_and_close(self, won: bool) -> None:
        try:
            self.store.save(self.state)
        except Exception as e:
            self._log(f"⚠ Ошибка сохранения: {e}")
        self.dismiss({
            "action": "battle_end",
            "won": won,
            "remaining": sum(1 for e in self._all_enemies if e.hp > 0),
            "destroyed": sum(1 for e in self._all_enemies if e.hp <= 0),
            "xp": self.state.xp,
        })

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-attack":
            self.action_attack()
        elif bid == "btn-rewrite":
            self.action_rewrite()
        elif bid == "btn-skip":
            self.action_skip()
        else:
            self.action_flee()
