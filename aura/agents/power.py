"""
Агент питания.

Управляет: выключение, перезагрузка, sleep, lock, logout.
Не имеет внешних зависимостей, кроме subprocess.

По науке:
- Изолирован
- Тестируем
- Не знает про AuraCore
"""

from __future__ import annotations

import subprocess

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentPower(BaseAgent):
    """
    Агент системных команд питания.

    Обрабатывает:
    - "выключи пк" / "poweroff" → shutdown
    - "перезагрузи" / "reboot" → reboot
    - "спящий режим" / "sleep" → suspend
    - "заблокируй" / "lock" → lock
    - "выйди из системы" / "logout" → logout
    """

    name = "power"
    MODULE_ALWAYS = True

    SHUTDOWN_KEYWORDS = ("выключи", "выключить", "poweroff", "shutdown")
    REBOOT_KEYWORDS = ("перезагрузи", "перезагрузить", "reboot", "restart")
    SUSPEND_KEYWORDS = ("спящий", "сон", "suspend", "sleep")
    LOCK_KEYWORDS = ("заблокируй", "заблокировать", "блок", "lock")
    LOGOUT_KEYWORDS = ("выйди из системы", "logout", "log out")
    HIBERNATE_KEYWORDS = ("гибернация", "hibernate")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        keywords = (
            self.SHUTDOWN_KEYWORDS
            + self.REBOOT_KEYWORDS
            + self.SUSPEND_KEYWORDS
            + self.LOCK_KEYWORDS
            + self.LOGOUT_KEYWORDS
            + self.HIBERNATE_KEYWORDS
        )
        return any(kw in text for kw in keywords)

    # Bug: необратимые действия без confirm
    NEEDS_CONFIRM = frozenset({"shutdown", "reboot", "logout", "hibernate"})
    CONFIRM_KEYWORDS = ("да", "подтверждаю", "точно", "yes", "конечно", "выполняй")
    CANCEL_KEYWORDS = ("нет", "отмена", "отменить", "не надо", "стоп", "cancel")

    _pending = None  # class-level: что ждёт подтверждения

    def _act(self, kind: str) -> str:
        return {
            "shutdown": self._shutdown,
            "reboot": self._reboot,
            "suspend": self._suspend,
            "lock": self._lock,
            "logout": self._logout,
            "hibernate": self._hibernate,
        }[kind]()

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        # Ждём подтверждения
        if AgentPower._pending:
            pending = AgentPower._pending
            if any(kw in text for kw in self.CONFIRM_KEYWORDS):
                AgentPower._pending = None
                return AgentResponse.ok(self._act(pending), self.name)
            if any(kw in text for kw in self.CANCEL_KEYWORDS):
                AgentPower._pending = None
                return AgentResponse.ok("❌ Отменено", self.name)
            return AgentResponse.ok(
                f"Жду подтверждения: «{pending}». Скажи «да» или «нет»",
                self.name,
            )

        # Определяем действие
        kind = None
        if any(kw in text for kw in self.SHUTDOWN_KEYWORDS):
            kind = "shutdown"
        elif any(kw in text for kw in self.REBOOT_KEYWORDS):
            kind = "reboot"
        elif any(kw in text for kw in self.HIBERNATE_KEYWORDS):
            kind = "hibernate"
        elif any(kw in text for kw in self.LOGOUT_KEYWORDS):
            kind = "logout"
        elif any(kw in text for kw in self.SUSPEND_KEYWORDS):
            kind = "suspend"
        elif any(kw in text for kw in self.LOCK_KEYWORDS):
            kind = "lock"

        if kind is None:
            return AgentResponse.not_handled(self.name)

        if kind in self.NEEDS_CONFIRM:
            AgentPower._pending = kind
            labels = {"shutdown": "Выключить ПК",
                      "reboot": "Перезагрузить ПК",
                      "logout": "Выйти из системы",
                      "hibernate": "Гибернация"}
            return AgentResponse.ok(
                f"⚠️ {labels[kind]}? Скажи «да» или «нет»", self.name
            )

        return AgentResponse.ok(self._act(kind), self.name)

    # --- Реализация ---

    def _shutdown(self) -> str:
        try:
            subprocess.Popen(
                ["systemctl", "poweroff"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return "💤 Выключаю ПК. До встречи!"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def _reboot(self) -> str:
        try:
            subprocess.Popen(
                ["systemctl", "reboot"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return "🔄 Перезагружаю ПК. Скоро вернусь!"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def _suspend(self) -> str:
        try:
            subprocess.Popen(
                ["systemctl", "suspend"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return "😴 Ухожу в сон. Разбуди, когда нужно."
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def _lock(self) -> str:
        try:
            subprocess.Popen(
                ["loginctl", "lock-session"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return "🔒 Экран заблокирован."
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def _logout(self) -> str:
        try:
            import os

            user = os.environ.get("USER", "user")
            subprocess.Popen(
                ["loginctl", "terminate-user", user],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return "🚪 Выхожу из системы."
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def _hibernate(self) -> str:
        try:
            subprocess.Popen(
                ["systemctl", "hibernate"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return "💤 Ухожу в гибернацию."
        except Exception as e:
            return f"❌ Ошибка: {e}"


__all__ = ["AgentPower"]
