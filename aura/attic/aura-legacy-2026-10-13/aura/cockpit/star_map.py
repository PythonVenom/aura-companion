"""F-088: Textual star map for Aura.

Визуальная карта секторов. X3 + Mass Effect vibe.
"""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Log, Static

from aura.cockpit.battle import BattleScreen
from aura.cockpit.task_battle import TaskBattleScreen
from aura.game.state import StateStore
from aura.lore.advisors import ADVISORS, advisor_speak
from aura.lore.campaign import (
    SECTORS,
    can_jump,
    get_current,
    get_next,
    open_tasks,
    sector_progress,
)
from aura.lore.tech_tree import render_tree


class TechScreen(ModalScreen):
    """F-093b: Дерево технологий в модалке."""

    CSS = """
    TechScreen { align: center middle; }
    #tech-box {
        width: 85%;
        height: 85%;
        border: thick #00ffff;
        background: #001820;
        padding: 1 2;
    }
    #tech-title { text-style: bold; color: #00ffff; padding: 0 0 1 0; }
    #tech-body { padding: 1 0; }
    #tech-actions { height: 3; }
    #tech-actions Button { margin: 0 1; }
    """

    BINDINGS = [("escape", "dismiss", "Закрыть")]

    def compose(self) -> ComposeResult:
        from aura.game.state import StateStore
        s = StateStore().load()
        with Container(id="tech-box"):
            yield Static("🎯  ДЕРЕВО ТЕХНОЛОГИЙ", id="tech-title")
            yield Static(render_tree(s), id="tech-body")
            with Horizontal(id="tech-actions"):
                yield Button("Закрыть [Esc]", id="btn-close", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)


class SectorDetail(ModalScreen):
    """Модальное окно деталей сектора (F-090)."""

    BINDINGS = [
        ("escape", "dismiss", "Закрыть"),
    ]

    def __init__(self, name: str) -> None:
        super().__init__()
        self.sector_name = name

    def compose(self) -> ComposeResult:
        meta = SECTORS.get(self.sector_name, {})
        title = meta.get("title", "?")
        chapter = meta.get("chapter", "?")
        desc = meta.get("desc", "—")
        nxt = meta.get("next")

        # Собрать модули сектора (пока — активные модули из state)
        try:
            s = StateStore().load()
            active = getattr(s, "modules_working", 0) or 0
            broken = getattr(s, "modules_broken", 0) or 0
            progress = getattr(s, "progress", 0.0)
        except Exception:
            active, broken, progress = 0, 0, 0.0

        # F-090b: список модулей (агентов) — реальные данные
        mod_list = ""
        try:
            from aura.bootstrap import build_orchestrator
            o = build_orchestrator()
            names = sorted(o.registry.list_names())[:10]
            mod_list = "\n".join(f"  • {n}" for n in names)
            if len(o.registry) > 10:
                mod_list += f"\n  ... ещё {len(o.registry) - 10}"
        except Exception:
            mod_list = "  (не удалось загрузить)"

        with Container(id="detail-box"):
            yield Static(
                f"📖  {self.sector_name} · глава {chapter} · {title}",
                id="detail-title",
            )
            sec = SECTORS.get(self.sector_name, {})
            prog = sector_progress(self.sector_name)
            tasks = SECTORS.get(self.sector_name, {}).get("tasks", [])
            task_lines = []
            for t in tasks[:8]:
                mark = "OK" if t.get("done") else "  "
                task_lines.append(f"  [{mark}] {t['id']:8} {t['title']}")
            tasks_str = chr(10).join(task_lines) if task_lines else "  (нет)"

            body = (
                f"{desc}" + chr(10) + chr(10)
                + "--- Прогресс ---" + chr(10)
                + f"Задач: {prog['done']}/{prog['total']} ({prog['pct']}%)" + chr(10)
                + f"Статус: {'ЗАКРЫТ' if prog['is_closed'] else 'В работе'}" + chr(10)
                + f"Prev: {sec.get('prev') or '-'}" + chr(10)
                + f"Next: {nxt or '-'}" + chr(10) + chr(10)
                + "--- Задачи ---" + chr(10)
                + tasks_str + chr(10) + chr(10)
                + "--- Корабль ---" + chr(10)
                + f"Модулей: {active}  Пробоин: {broken}  Сборка: {progress:.1f}%"
            )
            yield Static(body, id="detail-body")
            prev_name = sec.get("prev")
            next_name = sec.get("next")
            open_cnt = len(open_tasks(self.sector_name))

            with Horizontal(id="detail-actions"):
                if prev_name:
                    yield Button(f"< {prev_name}", id="btn-prev", variant="warning")
                # F-101c: скрыть ATK для секторов-горизонтов
                _sector_meta = SECTORS.get(self.sector_name, {})
                _can_attack = _sector_meta.get("attackable", True)
                if open_cnt and _can_attack:
                    yield Button(f"ATK ({open_cnt})", id="btn-attack", variant="error")
                elif open_cnt and not _can_attack:
                    yield Button("HORIZON", id="btn-horizon",
                             variant="default", disabled=True)
                yield Button("Jump here", id="btn-jump", variant="success")
                if next_name:
                    yield Button(f"{next_name} >", id="btn-next", variant="warning")
                yield Button("Close [Esc]", id="btn-close", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-jump":
            self.dismiss({"action": "jump", "target": self.sector_name})
        elif bid == "btn-attack":
            self.dismiss({"action": "task_battle", "target": self.sector_name})
        elif bid == "btn-prev":
            prev = SECTORS.get(self.sector_name, {}).get("prev")
            if prev:
                self.dismiss({"action": "jump", "target": prev})
        elif bid == "btn-next":
            nxt = SECTORS.get(self.sector_name, {}).get("next")
            if nxt:
                self.dismiss({"action": "jump", "target": nxt})
        else:
            self.dismiss(None)


class AuraMapApp(App):
    """Карта секторов Aura."""

    CSS = """
    Screen { background: #001018; color: #00ff88; }
    #left { width: 55%; border: solid #00ff88; padding: 1; }
    #right { width: 45%; border: solid #00ffff; padding: 1; }
    #map-title { text-style: bold; padding: 0 0 1 0; }
    .sector { padding: 0 1; }
    .sector-current { background: #003030; text-style: bold; }
    #log { height: 8; border: solid #444444; }
    SectorDetail { align: center middle; }
    #detail-box {
        width: 70%;
        height: auto;
        max-height: 80%;
        border: thick #00ffff;
        background: #001820;
        padding: 1 2;
    }
    #detail-title { text-style: bold; color: #00ffff; padding: 0 0 1 0; }
    #detail-body { padding: 1 0; }
    #detail-actions { height: 3; padding: 1 0 0 0; }
    #detail-actions Button { margin: 0 1; }
    """

    BINDINGS = [
        Binding("q", "quit", "Выход"),
        Binding("j", "jump", "Прыжок"),
        Binding("r", "refresh", "Обновить"),
        Binding("up", "cursor_up", "↑"),
        Binding("down", "cursor_down", "↓"),
        Binding("enter", "select", "Открыть"),
        Binding("escape", "deselect", "Закрыть"),
        Binding("b", "battle", "Бой"),
        Binding("v", "advisor", "Советник"),
        Binding("t", "tech", "Технологии"),
    ]

    def __init__(self) -> None:
        self._current = "?"
        self._visited: set[str] = {"FORMALIZE"}
        self._cursor: str = "FORMALIZE"
        super().__init__()
        self.store = StateStore()
        self.state = self.store.load()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="left"):
                yield Static("🗺️  КАРТА СЕКТОРОВ", id="map-title")
                for name in SECTORS:
                    yield Static(f"  {name}", classes="sector", id=f"node-{name}")
            with Vertical(id="right"):
                yield Static("", id="hud")
        yield Log(id="log")
        yield Footer()

    def on_mount(self) -> None:
        self._current = get_current()
        for name in SECTORS:
            self._refresh_node(name)
        self._refresh_hud()
        self._log(f"Карта загружена. Сектор: {self._current}")

    def _node_text(self, name: str) -> Static:
        meta = SECTORS[name]
        if name == self._current:
            mark = "🎯"
        elif name in self._visited:
            mark = "✓ "
        else:
            mark = "🔒"
        cls = "sector sector-current" if name == self._current else "sector"
        text = f"[{mark}] {name:12} · гл.{meta['chapter']} · {meta['title']}"
        return Static(text, classes=cls, id=f"node-{name}")

    def _refresh_hud(self) -> None:
        s = self.state
        hud = self.query_one("#hud", Static)
        mods_count = getattr(s, "modules_working", 0) or 0
        _sp = sector_progress(self._current)
        _sec_done = _sp["done"]
        _sec_total = _sp["total"]
        _sec_pct = _sp["pct"]
        hud.update(
            f"🛸  AURA · {getattr(s, 'rank', '?')}\n"
            "────────────────────\n"
            f"XP:        {getattr(s, 'xp', 0)}\n"
            f"Сектор:    {getattr(s, 'sector', '?')}\n"
            f"Прогресс:  {getattr(s, 'progress', 0):.1f}%\n"
            f"Корпус:    {min(100, getattr(s, 'hull', 0))}%\n"
            f"Щиты:      {getattr(s, 'shields', 0)}%\n"
            f"Реактор:   {getattr(s, 'reactor', 0)}%\n"
            f"Модулей:   {mods_count}\n"
            f"--- Сектор {self._current} ---\n"
            f"  Задач:  {_sec_done}/{_sec_total} ({_sec_pct}%)\n"
            "────────────────────\n"
            "Нажми:\n"
            "  ↑ ↓ — курсор\n"
            "  Enter — открыть\n"
            "  b   — бой\n"
            "  v   — советник\n"
            "  t   — технологии\n"
            "  j   — прыжок\n"
            "  r   — обновить\n"
            "  q   — выход"
        )

    def _log(self, msg: str) -> None:
        log = self.query_one("#log", Log)
        log.write_line(msg)

    def _refresh_node(self, name: str) -> None:
        meta = SECTORS[name]
        if name == self._current:
            mark = "🎯"
        elif name in self._visited:
            mark = "✓ "
        else:
            mark = "🔒"
        pointer = "▶ " if name == self._cursor else "  "
        cls = "sector sector-current" if name == self._current else "sector"
        node = self.query_one(f"#node-{name}", Static)
        node.update(
            f"{pointer}[{mark}] {name:12} · гл.{meta['chapter']} · {meta['title']}"
        )
        node.set_classes(cls)

    def _refresh_all_nodes(self) -> None:
        for name in SECTORS:
            self._refresh_node(name)

    def action_cursor_up(self) -> None:
        names = list(SECTORS.keys())
        i = names.index(self._cursor)
        self._cursor = names[(i - 1) % len(names)]
        self._refresh_all_nodes()
        self._log(f"↑ {self._cursor}")

    def action_cursor_down(self) -> None:
        names = list(SECTORS.keys())
        i = names.index(self._cursor)
        self._cursor = names[(i + 1) % len(names)]
        self._refresh_all_nodes()
        self._log(f"↓ {self._cursor}")

    def action_go_prev(self) -> None:
        """Откат к предыдущему сектору."""
        prev_name = SECTORS.get(self._current, {}).get("prev")
        if not prev_name:
            self._log("Первый сектор.")
            return
        self._do_jump(prev_name, force=True)

    def action_go_next(self) -> None:
        """Прыжок вперёд с проверкой."""
        next_name = SECTORS.get(self._current, {}).get("next")
        if not next_name:
            self._log("Последний сектор.")
            return
        self._do_jump(next_name, force=False)

    def action_select(self) -> None:
        """F-090: Enter — открыть детали сектора."""
        self.push_screen(SectorDetail(self._cursor), self._on_detail_dismiss)

    def _on_detail_dismiss(self, result) -> None:
        if not result:
            return
        action = result.get("action")
        if action == "task_battle":
            self.push_screen(TaskBattleScreen(result["target"]),
                             self._on_task_battle_end)
            return
        if action == "jump":
            target = result["target"]
            if target == self._current:
                self._log(f"Уже в {target}")
                return
            cur_ch = SECTORS.get(self._current, {}).get("chapter", 0)
            tgt_ch = SECTORS.get(target, {}).get("chapter", 0)
            force = tgt_ch < cur_ch
            self._do_jump(target, force=force)

    def _on_task_battle_end(self, result) -> None:
        self._refresh_all_nodes()
        self._refresh_hud()
        self._log("Battle done")

    def _do_jump(self, target: str, force: bool = False) -> None:
        """Прыжок в указанный сектор. force=True — обход can_jump."""
        if not force:
            ok, msg = can_jump(self._current, target)
            if not ok:
                self._log(msg)
                return
        old = self._current
        self.state.sector = target
        self.store.save(self.state)
        self._visited.add(old)
        self._current = target
        self._visited.add(target)
        self._cursor = target
        self._refresh_all_nodes()
        self._refresh_hud()
        self._log(f"✓ Сектор: {old} → {target}")

    def action_deselect(self) -> None:
        self._log("Esc")

    def action_tech(self) -> None:
        """t — дерево технологий."""
        self.push_screen(TechScreen(), None)

    def action_advisor(self) -> None:
        """v — советник говорит про текущий сектор."""
        import random
        key = random.choice(list(ADVISORS.keys()))
        adv = ADVISORS[key]

        # Определить контекст: сколько пробоин в state
        try:
            s = self.store.load()
            broken = getattr(s, "modules_broken", 0) or 0
        except Exception:
            broken = 0

        context = "sector_clean" if broken == 0 else "sector_dirty"
        kwargs = {"n": broken, "sector": self._current, "next": get_next(self._current) or "—"}
        line = advisor_speak(key, context, **kwargs) or adv.motto

        # Лог + голос
        self._log(f"{adv.emoji} {adv.name} ({adv.role}): {line}")
        try:
            from aura.voice.orchestrator import get_voice
            get_voice().say_text(f"{adv.name}. {line}")
        except Exception:
            pass

    def action_battle(self) -> None:
        """b — бой в текущем секторе."""
        self.push_screen(BattleScreen(self._current), self._on_battle_end)

    def _on_battle_end(self, result) -> None:
        if not result:
            return
        destroyed = result.get("destroyed", 0)
        remaining = result.get("remaining", 0)
        xp = result.get("xp", 0)
        if destroyed and not remaining:
            self._log(f"🎉 Победа! Уничтожено: {destroyed}. XP: {xp}")
        elif destroyed:
            self._log(f"⚔ Уничтожено: {destroyed}, осталось: {remaining}. XP: {xp}")
        else:
            self._log(f"🏃 Отступил. Уничтожено: {destroyed}. XP: {xp}")

    def action_refresh(self) -> None:
        self.state = self.store.load()
        self._current = get_current()
        self._cursor = self._current
        self._refresh_all_nodes()
        self._refresh_hud()
        self._log("⟳ Обновлено")

    def action_jump(self) -> None:
        """j — прыжок в следующий сектор."""
        nxt = get_next(self._current)
        if not nxt:
            self._log("🏁 Последний сектор. Прыгать некуда.")
            return
        self._do_jump(nxt)


if __name__ == "__main__":
    AuraMapApp().run()
