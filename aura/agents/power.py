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

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        if any(kw in text for kw in self.SHUTDOWN_KEYWORDS):
            return AgentResponse.ok(self._shutdown(), self.name)
        if any(kw in text for kw in self.REBOOT_KEYWORDS):
            return AgentResponse.ok(self._reboot(), self.name)
        if any(kw in text for kw in self.SUSPEND_KEYWORDS):
            return AgentResponse.ok(self._suspend(), self.name)
        if any(kw in text for kw in self.LOCK_KEYWORDS):
            return AgentResponse.ok(self._lock(), self.name)
        if any(kw in text for kw in self.LOGOUT_KEYWORDS):
            return AgentResponse.ok(self._logout(), self.name)
        if any(kw in text for kw in self.HIBERNATE_KEYWORDS):
            return AgentResponse.ok(self._hibernate(), self.name)

        return AgentResponse.not_handled(self.name)

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
