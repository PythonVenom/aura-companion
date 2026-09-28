"""Aura Telegram Bot (ADR-041) — skeleton.

Тонкий клиент: Telegram ⇄ Bot ⇄ Aura Core (JSON-RPC локально).
Token: env AURA_TG_TOKEN или ~/.config/aura/telegram_token

Graceful: если python-telegram-bot не установлен — не падаем.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path


TOKEN_ENV = "AURA_TG_TOKEN"
TOKEN_FILE = Path.home() / ".config" / "aura" / "telegram_token"
ADMIN_IDS_ENV = "AURA_TG_ADMIN_IDS"


def load_token() -> str:
    tok = os.environ.get(TOKEN_ENV, "")
    if tok:
        return tok.strip()
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    return ""


def load_admin_ids() -> set[int]:
    raw = os.environ.get(ADMIN_IDS_ENV, "")
    out = set()
    for x in raw.split(","):
        x = x.strip()
        if x.isdigit():
            out.add(int(x))
    return out


class AuraBot:
    """Минимальный бот: 3 команды + voice.command в ядро."""

    def __init__(self, token: str | None = None) -> None:
        self.token = token or load_token()
        self.admins = load_admin_ids()
        self._app = None

    def is_ready(self) -> bool:
        if not self.token:
            return False
        try:
            import telegram  # noqa: F401
        except ImportError:
            return False
        return True

    async def _cmd_start(self, update, context):
        await update.message.reply_text(
            "Aura bot online. Команды:
"
            "/status — статус ядра
"
            "/voice <текст> — голосовая команда в Aura
"
            "/timer 5m чай — таймер"
        )

    async def _cmd_status(self, update, context):
        try:
            from aura.bootstrap import build_orchestrator
            orch = build_orchestrator()
            await update.message.reply_text(f"✅ Ядро: {len(orch)} агентов")
        except Exception as e:
            await update.message.reply_text(f"❌ {e}")

    async def _cmd_voice(self, update, context):
        text = " ".join(context.args) if context.args else ""
        if not text:
            await update.message.reply_text("Использование: /voice <текст>")
            return
        try:
            from aura.bootstrap import build_orchestrator
            orch = build_orchestrator()
            result = await orch.process(text)
            await update.message.reply_text(result[:4000])
        except Exception as e:
            await update.message.reply_text(f"❌ {e}")

    async def _cmd_timer(self, update, context):
        if not context.args:
            await update.message.reply_text("Использование: /timer 5m чай")
            return
        try:
            from aura.agents import time_agent
            from aura.cli import _parse_duration
            dur = context.args[0]
            label = " ".join(context.args[1:]) or dur
            seconds = _parse_duration(dur)
            t = time_agent.add_timer(seconds, label)
            await update.message.reply_text(f"⏱ {t['label']} ({dur})")
        except Exception as e:
            await update.message.reply_text(f"❌ {e}")

    def build_app(self):
        from telegram.ext import ApplicationBuilder, CommandHandler
        app = ApplicationBuilder().token(self.token).build()
        app.add_handler(CommandHandler("start", self._cmd_start))
        app.add_handler(CommandHandler("status", self._cmd_status))
        app.add_handler(CommandHandler("voice", self._cmd_voice))
        app.add_handler(CommandHandler("timer", self._cmd_timer))
        self._app = app
        return app

    def run(self) -> None:
        if not self.is_ready():
            print("❌ Bot не готов: нет токена или python-telegram-bot")
            print(f"   pip install python-telegram-bot")
            print(f"   export {TOKEN_ENV}=<token from @BotFather>")
            return
        app = self.build_app()
        print(f"🤖 Aura bot запущен. Admins: {self.admins or 'все'}")
        app.run_polling()


def main() -> None:
    AuraBot().run()


if __name__ == "__main__":
    main()
