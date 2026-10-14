"""#39 Configurator — Textual TUI для редактирования профиля Aura.

Почему Textual, а не GTK4:
- Проект уже на Textual (cockpit/studio.py, form.py)
- Работает в AppImage, по SSH, без X11/Wayland
- +0 МБ зависимостей (GTK4 = +200 МБ)
- Единый стек (Textual + pytest)

Вкладки:
  👤 Профиль       — UserProfile (name, age, city)
  🔔 Уведомления   — история из notifications.db
  🔑 Ключи         — Ed25519 pubkey + rotate
  🤖 Агенты        — список 92 (read-only)
"""
from __future__ import annotations

import sqlite3

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
    TabbedContent,
    TabPane,
)


class ProfileTab(Container):
    """Редактирование UserProfile."""

    def compose(self) -> ComposeResult:
        from aura.core.profile import UserProfile
        p = UserProfile.load()
        yield Label(f"👤 Профиль: {p.name}", id="profile-title")
        yield Label("Имя:")
        yield Input(value=p.name, id="input-name", placeholder="captain")
        yield Label("Возраст:")
        yield Input(value=str(p.age or ""), id="input-age", placeholder="—")
        yield Label("Город:")
        yield Input(value=p.city or "", id="input-city", placeholder="—")
        yield Horizontal(
            Button("💾 Сохранить", id="btn-save", variant="success"),
            Button("🔄 Перезагрузить", id="btn-reload", variant="default"),
        )
        yield Static("", id="profile-status")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self._save()
        elif event.button.id == "btn-reload":
            self.app.refresh_profile()

    def _save(self) -> None:
        from aura.core.profile import UserProfile
        p = UserProfile.load()
        p.name = self.query_one("#input-name", Input).value or "captain"
        age_val = self.query_one("#input-age", Input).value.strip()
        p.age = int(age_val) if age_val.isdigit() else None
        p.city = self.query_one("#input-city", Input).value.strip() or None
        p.save()
        self.query_one("#profile-status", Static).update("✅ Сохранено в profile.json")


class NotificationsTab(Container):
    """История уведомлений P0-P3."""

    def compose(self) -> ComposeResult:
        yield DataTable(id="notif-table")

    def on_mount(self) -> None:
        table = self.query_one("#notif-table", DataTable)
        table.add_columns("Время", "Ур.", "Агент", "Заголовок", "Тело")
        from aura.core.notifications import DB
        if not DB.exists():
            return
        try:
            conn = sqlite3.connect(DB)
            rows = conn.execute(
                "SELECT ts, level, agent, title, body FROM history ORDER BY ts DESC LIMIT 50"
            ).fetchall()
            conn.close()
        except Exception:
            return
        from datetime import datetime
        lvl_names = {0: "P0", 1: "P1", 2: "P2", 3: "P3"}
        for ts, level, agent, title, body in rows:
            t = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
            table.add_row(t, lvl_names.get(level, "?"), agent or "—", title, body[:40])


class KeysTab(Container):
    """Ed25519-ключи профиля."""

    def compose(self) -> ComposeResult:
        yield Label("🔑 Ed25519 Public Key:")
        yield Static(self._pubkey(), id="pubkey-display")
        yield Button("🔁 Rotate Keypair", id="btn-rotate", variant="warning")
        yield Static("", id="key-status")

    def _pubkey(self) -> str:
        try:
            from aura.core.ledger import PUB_PATH, public_key_b64
            if not PUB_PATH.exists():
                return "(ключ ещё не сгенерирован — нажми Rotate)"
            return public_key_b64()
        except Exception as e:
            return f"(ошибка: {e})"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-rotate":
            from aura.core.ledger import generate_keypair
            generate_keypair(force=True)
            self.query_one("#pubkey-display", Static).update(self._pubkey())
            self.query_one("#key-status", Static).update("✅ Ключ пересоздан")


class AgentsTab(Container):
    """Список загруженных агентов (read-only)."""

    def compose(self) -> ComposeResult:
        yield ListView(id="agents-list")

    def on_mount(self) -> None:
        try:
            from aura.agents import __all__ as agents_all
            items = [ListItem(Label(name)) for name in sorted(agents_all)]
        except Exception:
            items = [ListItem(Label("(не удалось загрузить список агентов)"))]
        self.query_one("#agents-list", ListView).extend(items)


class ConfiguratorApp(App):
    """Главное приложение конфигуратора."""

    CSS = """
    TabbedContent { height: 1fr; }
    Container { padding: 1; }
    Input { margin-bottom: 1; }
    Button { margin-right: 1; }
    #profile-status, #key-status { margin-top: 1; color: green; }
    #pubkey-display { background: $surface; padding: 1; margin-bottom: 1; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent():
            with TabPane("👤 Профиль", id="tab-profile"):
                yield ProfileTab()
            with TabPane("🔔 Уведомления", id="tab-notif"):
                yield NotificationsTab()
            with TabPane("🔑 Ключи", id="tab-keys"):
                yield KeysTab()
            with TabPane("🤖 Агенты", id="tab-agents"):
                yield AgentsTab()
        yield Footer()

    def action_refresh(self) -> None:
        self.refresh_profile()

    def refresh_profile(self) -> None:
        """Перечитать профиль из файла."""
        try:
            tab = self.query_one(ProfileTab)
            from aura.core.profile import UserProfile
            p = UserProfile.load()
            tab.query_one("#input-name", Input).value = p.name
            tab.query_one("#input-age", Input).value = str(p.age or "")
            tab.query_one("#input-city", Input).value = p.city or ""
            tab.query_one("#profile-status", Static).update("🔄 Перезагружено")
        except Exception:
            pass


def main() -> None:
    ConfiguratorApp().run()


if __name__ == "__main__":
    main()


__all__ = ["ConfiguratorApp", "main"]
