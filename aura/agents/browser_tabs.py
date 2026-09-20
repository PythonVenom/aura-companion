"""
Агент управления вкладками Firefox.

Работает через Unix socket, к которому подключается native-messaging bridge.
Протокол: JSON-строки, разделённые \n.

По науке:
- Изолирован (только socket)
- Тестируем (mock для socket)
- Не знает про AuraCore
- Без Firefox в тестах — только mock
"""

from __future__ import annotations

import json
import socket

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentBrowserTabs(BaseAgent):
    """
    Агент управления вкладками Firefox.

    Обрабатывает:
    - "новая вкладка" / "открой вкладку" → new_tab
    - "закрой вкладку" → close_tab
    - "следующая вкладка" → next_tab
    - "предыдущая вкладка" → prev_tab
    - "список вкладок" → list_tabs
    """

    name = "browser_tabs"

    NEW_KEYWORDS = ("новая вкладка", "открой вкладку", "открыть вкладку")
    CLOSE_KEYWORDS = ("закрой вкладку", "закрыть вкладку")
    NEXT_KEYWORDS = ("следующая вкладка", "следующую вкладку", "вперёд вкладку")
    PREV_KEYWORDS = ("предыдущая вкладка", "предыдущую вкладку", "назад вкладку")
    LIST_KEYWORDS = ("список вкладок", "какие вкладки", "открытые вкладки")

    def __init__(self, socket_path: str = "/tmp/aura_firefox.sock") -> None:
        super().__init__()
        self.socket_path = socket_path

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        keywords = (
            self.NEW_KEYWORDS
            + self.CLOSE_KEYWORDS
            + self.NEXT_KEYWORDS
            + self.PREV_KEYWORDS
            + self.LIST_KEYWORDS
        )
        return any(kw in text for kw in keywords)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        if any(kw in text for kw in self.LIST_KEYWORDS):
            return AgentResponse.ok(self.list_tabs(), self.name)

        if any(kw in text for kw in self.NEW_KEYWORDS):
            return AgentResponse.ok(self.new_tab(), self.name)

        if any(kw in text for kw in self.CLOSE_KEYWORDS):
            return AgentResponse.ok(self.close_tab(), self.name)

        if any(kw in text for kw in self.NEXT_KEYWORDS):
            return AgentResponse.ok(self.next_tab(), self.name)

        if any(kw in text for kw in self.PREV_KEYWORDS):
            return AgentResponse.ok(self.prev_tab(), self.name)

        return AgentResponse.not_handled(self.name)

    # --- Внутренние методы ---

    def _send_command(self, cmd: dict) -> dict | None:
        """Отправить команду в bridge и получить ответ."""
        try:
            payload = (json.dumps(cmd) + "\n").encode("utf-8")
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(3.0)
                s.connect(self.socket_path)
                s.sendall(payload)
                data = s.recv(65536)
            if not data:
                return None
            return json.loads(data.decode("utf-8").strip())
        except FileNotFoundError:
            return {"error": "bridge_not_running"}
        except socket.timeout:
            return {"error": "timeout"}
        except Exception as e:
            return {"error": str(e)}

    def new_tab(self) -> str:
        result = self._send_command({"action": "new_tab"})
        if result is None or "error" in result:
            return self._error_text(result)
        return "🌐 Открыла новую вкладку"

    def close_tab(self) -> str:
        result = self._send_command({"action": "close_tab"})
        if result is None or "error" in result:
            return self._error_text(result)
        return "🌐 Закрыла вкладку"

    def next_tab(self) -> str:
        result = self._send_command({"action": "next_tab"})
        if result is None or "error" in result:
            return self._error_text(result)
        return "🌐 Переключилась на следующую вкладку"

    def prev_tab(self) -> str:
        result = self._send_command({"action": "prev_tab"})
        if result is None or "error" in result:
            return self._error_text(result)
        return "🌐 Переключилась на предыдущую вкладку"

    def list_tabs(self) -> str:
        result = self._send_command({"action": "list_tabs"})
        if result is None or "error" in result:
            return self._error_text(result)
        tabs = result.get("tabs", [])
        if not tabs:
            return "🌐 Открытых вкладок нет"
        out = [f"🌐 Вкладок: {len(tabs)}"]
        for i, t in enumerate(tabs[:15], 1):
            title = t.get("title", "?")
            out.append(f"{i}. {title}")
        return "\n".join(out)

    @staticmethod
    def _error_text(result: dict | None) -> str:
        if result is None:
            return "❌ Firefox bridge не ответил"
        err = result.get("error", "unknown")
        if err == "bridge_not_running":
            return "❌ Firefox bridge не запущен"
        if err == "timeout":
            return "❌ Firefox не ответил вовремя"
        return f"❌ Ошибка bridge: {err}"


__all__ = ["AgentBrowserTabs"]
