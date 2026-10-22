"""F-100: ScanScreen — что болит у корабля.

Модалка: список реальных проблем (из ruff через spawner).
Enter на проблеме → бой (run_guided).
Победа → XP + журнал.
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from aura.game.spawner import spawn_enemies_from_ruff


class ScanScreen(ModalScreen):
    """Сканер проблем сектора."""

    CSS = """
    ScanScreen { align: center middle; }
    #scan-box {
        width: 85%;
        height: 75%;
        border: thick #00ffff;
        background: #001820;
        padding: 1 2;
    }
    #scan-title { text-style: bold; color: #00ffff; padding: 0 0 1 0; }
    #scan-body { padding: 1 0; }
    #scan-actions { height: 3; }
    #scan-actions Button { margin: 0 1; }
    """

    BINDINGS = [("escape", "dismiss", "Закрыть")]

    def __init__(self, sector: str) -> None:
        super().__init__()
        self.sector = sector
        self.fleet = []
        for target in ("aura/", "scripts/"):
            self.fleet.extend(spawn_enemies_from_ruff(target))

    def compose(self) -> ComposeResult:
        with Container(id="scan-box"):
            if not self.fleet:
                title = "✅ СЕКТОР ЧИСТ"
                body = "Пробоин нет. Корабль в норме."
            else:
                title = f"⚠️  ОБНАРУЖЕНО: {len(self.fleet)} пробоин"
                lines = []
                for i, e in enumerate(self.fleet[:20], 1):
                    icon = {"drone": "🛸", "interceptor": "⚡",
                            "frigate": "🚀", "leviathan": "🐙"}.get(
                        e.enemy_type, "👾")
                    lines.append(
                        f"  {i:2}. {icon} [{e.name}] {e.sector}:{e.line}"
                    )
                if len(self.fleet) > 20:
                    lines.append(f"  ... и ещё {len(self.fleet) - 20}")
                body = "\n".join(lines)

            yield Static(f"🔭 {title}", id="scan-title")
            yield Static(body, id="scan-body")
            with Horizontal(id="scan-actions"):
                if self.fleet:
                    yield Button("Исправить всё [F]", id="btn-fix", variant="error")
                yield Button("Закрыть [Esc]", id="btn-close", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-fix":
            self._fix_all()
        else:
            self.dismiss(None)

    def _fix_all(self) -> None:
        """F-100b: AUTO-FIX без интерактива.

        Для TUI: не спрашиваем оружие — применяем стратегию паттерна напрямую.
        Промахов нет — ruff-ошибка имеет детерминированный фикс.
        """
        from aura.game.problem import Problem
        from aura.game.state import StateStore
        from aura.lore.story import StoryLog

        killed = 0
        results = []

        for e in self.fleet:
            p = Problem(
                code=e.name, sector=e.sector, line=e.line,
                raw_message=getattr(e, "message", ""),
            )
            # Применяем рекомендованную стратегию напрямую
            strategy = p.pattern.strategy
            try:
                ok, msg = p.try_solve(strategy)
                if ok:
                    killed += 1
                    results.append(f"✅ {e.name} — решено ({strategy})")
                else:
                    results.append(f"⚠️ {e.name} — {msg}")
            except Exception as ex:
                results.append(f"❌ {e.name} — {ex}")

        # Награда: XP за каждую решённую пробоину
        if killed > 0:
            try:
                store = StateStore()
                st = store.load()
                xp_reward = killed * 15
                st.add_xp(xp_reward)
                # Пересчёт пробоин
                st.modules_broken = max(0, st.modules_broken - killed)
                st.recalc_progress()
                store.save(st)
                store.close()

                # В журнал
                story = StoryLog()
                story.log_maneuver(
                    commit=f"AUTOFIX-{killed}",
                    description=f"Починено пробоин: {killed}",
                    day=1,
                    sector="FORMALIZE",
                )
            except Exception as ex:
                results.append(f"⚠️ State: {ex}")

        self.dismiss({
            "killed": killed,
            "total": len(self.fleet),
            "results": results,
        })
