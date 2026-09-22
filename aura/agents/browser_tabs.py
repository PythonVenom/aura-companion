"""
Агент управления вкладками Firefox.

Работает через Unix socket с native-messaging bridge.
Протокол: 4 байта длины (LE) + JSON.

По науке:
- Изолирован (только socket)
- Тестируем (mock для socket)
- Не знает про AuraCore
- Без Firefox в тестах — только mock

Боль из промта:
- «Открой ВК» создавал новую вкладку вместо фокуса на открытой.
  Решение: сначала find_tab, если найдено — activate, иначе open.

См. ADR-004, Фаза 8.
"""

from __future__ import annotations

import json
import socket
import struct

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


# Известные URL для «открой X»
KNOWN_URLS = {
    "вк": "https://vk.com",
    "вконтакте": "https://vk.com",
    "vk": "https://vk.com",
    "телеграм": "https://web.telegram.org",
    "телега": "https://web.telegram.org",
    "тг": "https://web.telegram.org",
    "telegram": "https://web.telegram.org",
    "ютуб": "https://youtube.com",
    "youtube": "https://youtube.com",
    "макс": "https://max.ru",
    "max": "https://max.ru",
    "deepseek": "https://chat.deepseek.com",
    "дипсик": "https://chat.deepseek.com",
    "гитхаб": "https://github.com",
    "github": "https://github.com",
}


class AgentBrowserTabs(BaseAgent):
    """
    Агент управления вкладками Firefox.

    Обрабатывает:
    - «какие вкладки» / «список вкладок» → list_tabs
    - «новая вкладка» → open_tab(about:newtab)
    - «закрой вкладку» → найти активную → close_tab
    - «закрой вкладку X» → close_tab_by_name
    - «следующая вкладка» → next_tab
    - «предыдущая вкладка» → prev_tab
    - «найди вкладку X» / «переключись на X» → find + activate
    - «открой X» (ВК, телеграм, ютуб...) → find, если нет — open
    """

    name = "browser_tabs"

    LIST_KEYWORDS = (
        "какие вкладки", "список вкладок", "открытые вкладки",
        "покажи вкладки", "что открыто",
    )
    NEW_KEYWORDS = ("новая вкладка", "открой вкладку", "открыть вкладку", "создай вкладку")
    CLOSE_KEYWORDS = ("закрой вкладку", "закрыть вкладку", "удали вкладку")
    NEXT_KEYWORDS = ("следующая вкладка", "следующую вкладку", "вперёд вкладку")
    PREV_KEYWORDS = ("предыдущая вкладка", "предыдущую вкладку", "назад вкладку")
    FIND_KEYWORDS = ("найди вкладку", "переключись на вкладку", "фокус на вкладку", "перейди на вкладку")
    OPEN_KEYWORDS = ("открой сайт", "открой страницу")

    def __init__(self, socket_path: str = "/tmp/aura_firefox.sock") -> None:
        super().__init__()
        self.socket_path = socket_path

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        # «открой вкладку» перехватывает NEW — но «открой X» (сайт) может быть find/open
        if any(kw in text for kw in self.NEW_KEYWORDS):
            return True
        all_kw = (
            self.LIST_KEYWORDS + self.CLOSE_KEYWORDS + self.NEXT_KEYWORDS
            + self.PREV_KEYWORDS + self.FIND_KEYWORDS + self.OPEN_KEYWORDS
        )
        if any(kw in text for kw in all_kw):
            return True
        # «открой вк», «открой телеграм» и т.п.
        if text.startswith("открой ") or text.startswith("открыть "):
            rest = text.split(" ", 1)[1] if " " in text else ""
            if any(name in rest for name in KNOWN_URLS):
                return True
        return False

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        if any(kw in text for kw in self.LIST_KEYWORDS):
            return AgentResponse.ok(self.list_tabs(), self.name)

        if any(kw in text for kw in self.NEW_KEYWORDS):
            return AgentResponse.ok(self.new_tab(), self.name)

        if any(kw in text for kw in self.CLOSE_KEYWORDS):
            # «закрой вкладку X» — закрыть по имени
            name = self._extract_after(text, self.CLOSE_KEYWORDS)
            if name:
                return AgentResponse.ok(self.close_tab_by_name(name), self.name)
            return AgentResponse.ok(self.close_active_tab(), self.name)

        if any(kw in text for kw in self.NEXT_KEYWORDS):
            return AgentResponse.ok(self.next_tab(), self.name)

        if any(kw in text for kw in self.PREV_KEYWORDS):
            return AgentResponse.ok(self.prev_tab(), self.name)

        if any(kw in text for kw in self.FIND_KEYWORDS):
            name = self._extract_after(text, self.FIND_KEYWORDS)
            if not name:
                return AgentResponse.ok("Какую вкладку искать?", self.name)
            return AgentResponse.ok(self.find_and_activate(name), self.name)

        # «открой X» — сначала find, иначе open url
        if text.startswith("открой ") or text.startswith("открыть "):
            rest = text.split(" ", 1)[1].strip()
            return AgentResponse.ok(self.open_or_focus(rest), self.name)

        return AgentResponse.not_handled(self.name)

    # --- Разбор аргумента ---

    @staticmethod
    def _extract_after(text: str, keywords: tuple[str, ...]) -> str:
        """Взять текст после ключевой фразы."""
        for kw in keywords:
            if kw in text:
                idx = text.index(kw) + len(kw)
                return text[idx:].strip().strip(".,!?").strip()
        return ""

    # --- Открытие/фокус ---

    def open_or_focus(self, what: str) -> str:
        """Найти открытую вкладку по имени/URL; если нет — открыть известный URL."""
        if not what:
            return "Что открыть?"

        # Нормализуем: если what — ключ из KNOWN_URLS, ищем по ключу + открываем url
        url = None
        search_term = what
        for key, u in KNOWN_URLS.items():
            if key in what:
                url = u
                search_term = key
                break

        # Сначала пытаемся найти уже открытую
        found = self._send_command({"action": "find_tab", "query": search_term})
        if found and "tabs" in found and found["tabs"]:
            tab = found["tabs"][0]
            tab_id = tab.get("id")
            if tab_id is not None:
                act = self._send_command({"action": "activate_tab", "tab_id": tab_id})
                if act and act.get("success"):
                    title = act.get("title", "?")
                    return f"🌐 Переключилась на «{title[:60]}»"
                return self._error_text(act)

        # Не нашли — открываем
        if url:
            res = self._send_command({"action": "open_tab", "url": url, "active": True})
            if res and res.get("success"):
                return f"🌐 Открыла {url}"
            return self._error_text(res)

        # Нет известного URL — поиск в Google
        res = self._send_command({"action": "new_tab_search", "query": what})
        if res and res.get("success"):
            return f"🌐 Ищу «{what[:60]}»"
        return self._error_text(res)

    def find_and_activate(self, query: str) -> str:
        """Найти вкладку и переключиться."""
        found = self._send_command({"action": "find_tab", "query": query})
        if not found or "error" in found:
            return self._error_text(found)
        tabs = found.get("tabs", [])
        if not tabs:
            return f"🌐 Вкладка «{query}» не найдена"
        tab = tabs[0]
        tab_id = tab.get("id")
        if tab_id is None:
            return "🌐 Найдена вкладка без id"
        act = self._send_command({"action": "activate_tab", "tab_id": tab_id})
        if act and act.get("success"):
            return f"🌐 Переключилась на «{act.get('title', query)[:60]}»"
        return self._error_text(act)

    # --- Команды ---

    def new_tab(self) -> str:
        result = self._send_command({"action": "open_tab", "url": "about:newtab", "active": True})
        if result is None or "error" in result:
            return self._error_text(result)
        return "🌐 Открыла новую вкладку"

    def close_active_tab(self) -> str:
        """Закрыть активную вкладку: найти её id через list_tabs."""
        listed = self._send_command({"action": "list_tabs"})
        if not listed or "error" in listed:
            return self._error_text(listed)
        tabs = listed.get("tabs", [])
        active = next((t for t in tabs if t.get("active")), None)
        if not active:
            return "🌐 Не нашла активную вкладку"
        tab_id = active.get("id")
        result = self._send_command({"action": "close_tab", "tab_id": tab_id})
        if result is None or "error" in result:
            return self._error_text(result)
        return "🌐 Закрыла вкладку"

    def close_tab_by_name(self, query: str) -> str:
        result = self._send_command({"action": "close_tab_by_name", "query": query})
        if result is None or "error" in result:
            if result and result.get("error") == "not found":
                return f"🌐 Вкладка «{query}» не найдена"
            return self._error_text(result)
        title = result.get("title", query)
        return f"🌐 Закрыла «{title[:60]}»"

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
            mark = "▶" if t.get("active") else " "
            title = t.get("title", "?")
            out.append(f"{mark} {i}. {title[:70]}")
        return "\n".join(out)

    # --- Протокол ---

    def _send_command(self, cmd: dict) -> dict | None:
        """Отправить команду (length-prefix) и получить ответ."""
        try:
            payload = json.dumps(cmd, ensure_ascii=False).encode("utf-8")
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(5.0)
                s.connect(self.socket_path)
                s.sendall(struct.pack("@I", len(payload)) + payload)

                # Читаем 4 байта длины + тело
                header = self._recv_exact(s, 4)
                if not header:
                    return None
                length = struct.unpack("@I", header)[0]
                body = self._recv_exact(s, length)
                if not body:
                    return None
                return json.loads(body.decode("utf-8"))
        except FileNotFoundError:
            return {"error": "bridge_not_running"}
        except socket.timeout:
            return {"error": "timeout"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def _recv_exact(s: socket.socket, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = s.recv(n - len(buf))
            if not chunk:
                return b""
            buf += chunk
        return buf

    @staticmethod
    def _error_text(result: dict | None) -> str:
        if result is None:
            return "❌ Firefox bridge не ответил"
        err = result.get("error", "unknown")
        if err == "bridge_not_running":
            return "❌ Firefox bridge не запущен (extension не загружен?)"
        if err == "timeout":
            return "❌ Firefox не ответил вовремя"
        if err == "not found":
            return "❌ Вкладка не найдена"
        return f"❌ Ошибка bridge: {err}"


__all__ = ["AgentBrowserTabs"]
