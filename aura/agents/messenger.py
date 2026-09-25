"""
Агент мессенджеров (AgentMessenger).

Фаза 13.2: работает с web.max.ru через Firefox bridge.
Чтение чатов, поиск, отправка сообщений.

По науке:
- Изолирован (только bridge через aura.core.bridge)
- Тестируем (mock bridge, живой Firefox не трогаем)
- Не знает про AuraCore
- Без Firefox в тестах — только mock

Сценарии из vision.md:
- «Аура, открой Макс» — фокус на вкладку.
- «Аура, какие чаты в Максе» — список.
- «Аура, найди чат с Иваном» — переключиться.
- «Аура, что написали?» — последнее сообщение.
- «Аура, напиши Ивану: ...» — ввод (без отправки, подтверждение отдельно).
"""

from __future__ import annotations

from aura.core.bridge import send_command, error_text
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentMessenger(BaseAgent):
    """
    Агент для Макса (и позже — других мессенджеров).

    Обрабатывает:
    - «открой макс» / «открой макс веб» — фокус.
    - «какие чаты в максе» / «список чатов макс» — list_chats.
    - «найди чат с X» / «открой чат X» — find_chat.
    - «что написали» / «прочитай макс» — read_last.
    - «напиши X сообщение Y» — send (ввод).
    """

    name = "messenger"

    OPEN_KEYWORDS = (
        "открой макс",
        "открыть макс",
        "макс веб",
    )
    LIST_KEYWORDS = (
        "какие чаты в максе",
        "список чатов макс",
        "покажи чаты макс",
        "что в максе",
    )
    FIND_KEYWORDS = (
        "найди чат",
        "открой чат",
        "перейди в чат",
    )
    READ_KEYWORDS = (
        "что написали",
        "прочитай макс",
        "прочитай чат",
        "новые сообщения",
    )
    SEND_KEYWORDS = (
        "напиши в макс",
        "напиши макс",
        "напиши сообщение",
        "отправь в макс",
    )

    # Только ошибочные формы T-one. «макс», «максе» — правильные.
    MAX_ALIASES = ("макте", "макт", "мактэ", "макст", "максу", "макса", "максы", "максэ", "максом")

    def _normalize(self, text: str) -> str:
        for alias in self.MAX_ALIASES:
            if alias in text:
                text = text.replace(alias, "макс")
        return text

    def can_handle(self, request: AgentRequest) -> bool:
        text = self._normalize(request.text.lower())
        all_kw = (
            self.OPEN_KEYWORDS + self.LIST_KEYWORDS + self.FIND_KEYWORDS
            + self.READ_KEYWORDS + self.SEND_KEYWORDS
        )
        if "макс" in text and any(kw in text for kw in all_kw):
            return True
        if "чат" in text and any(kw in text for kw in self.FIND_KEYWORDS):
            return True
        return False

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = self._normalize(request.text.lower())

        # 1. Открыть Макс — фокус на вкладку.
        if any(kw in text for kw in self.OPEN_KEYWORDS):
            return AgentResponse.ok(self.open_max(), self.name)

        # 2. Список чатов.
        if any(kw in text for kw in self.LIST_KEYWORDS):
            return AgentResponse.ok(self.list_chats(), self.name)

        # 3. Найти чат.
        if any(kw in text for kw in self.FIND_KEYWORDS):
            query = self._extract_chat_name(text)
            if not query:
                return AgentResponse.ok("Какой чат искать?", self.name)
            return AgentResponse.ok(self.find_chat(query), self.name)

        # 4. Прочитать последнее.
        if any(kw in text for kw in self.READ_KEYWORDS):
            return AgentResponse.ok(self.read_last(), self.name)

        # 5. Написать — извлекаем «кому» и «что».
        if any(kw in text for kw in self.SEND_KEYWORDS):
            chat, msg = self._extract_send(text)
            if not chat:
                return AgentResponse.ok("Кому написать?", self.name)
            if not msg:
                return AgentResponse.ok(f"Что написать {chat}?", self.name)
            return AgentResponse.ok(self.send_message(chat, msg), self.name)

        return AgentResponse.not_handled(self.name)

    # --- Команды ---

    def open_max(self) -> str:
        """Открыть/сфокусировать вкладку Макса."""
        result = send_command({"action": "open_tab", "url": "https://web.max.ru", "active": True})
        if result is None or "error" in result:
            return error_text(result)
        return "🌐 Открыла Макс"

    def list_chats(self) -> str:
        result = send_command({"action": "max_list_chats"})
        if result is None or "error" in result:
            return error_text(result)
        # Ответ приходит как {ok: true, data: {count, chats}}
        data = result.get("data", {})
        chats = data.get("chats", [])
        if not chats:
            return "🌐 Чатов не найдено. Открой Макс в Firefox."
        out = [f"🌐 Чатов: {len(chats)}"]
        for i, c in enumerate(chats[:15], 1):
            out.append(f"{i}. {c.get('name', '?')[:50]}")
        return "\n".join(out)

    def find_chat(self, query: str) -> str:
        result = send_command({"action": "max_find_chat", "query": query})
        if result is None or "error" in result:
            return error_text(result)
        data = result.get("data", {})
        if data.get("found"):
            name = data.get("name", query)
            return f"🌐 Открыла чат: {name[:60]}"
        return f"🌐 Чат «{query}» не найден"

    def read_last(self) -> str:
        result = send_command({"action": "max_read_last"})
        if result is None or "error" in result:
            return error_text(result)
        data = result.get("data", {})
        last = data.get("last", "")
        if not last:
            return "🌐 Нет новых сообщений"
        return f"🌐 Последнее сообщение: {last[:200]}"

    def send_message(self, chat: str, message: str) -> str:
        """Открыть чат, ввести текст (без отправки)."""
        # 1. Найти чат.
        find = send_command({"action": "max_find_chat", "query": chat})
        if find is None or "error" in find:
            return error_text(find)
        data = find.get("data", {})
        if not data.get("found"):
            return f"🌐 Чат «{chat}» не найден"

        # 2. Ввести текст.
        send = send_command({"action": "max_send_message", "text": message})
        if send is None or "error" in send:
            return error_text(send)
        sd = send.get("data", {})
        if sd.get("typed"):
            return (
                f"🌐 Открыла чат «{chat}», ввела текст. "
                f"Скажи «отправь» для отправки."
            )
        return "🌐 Не удалось ввести текст"

    # --- Разбор аргументов ---

    @staticmethod
    def _extract_chat_name(text: str) -> str:
        for kw in ("найди чат с", "найди чат", "открой чат с", "открой чат", "перейди в чат с", "перейди в чат"):
            if kw in text:
                idx = text.index(kw) + len(kw)
                rest = text[idx:].strip().strip(".,!?")
                if rest:
                    return rest
        return ""

    @staticmethod
    def _extract_send(text: str) -> tuple[str, str]:
        """Извлечь (кому, что) из «напиши маме: сегодня...»."""
        # Формат: «напиши X: Y» или «напиши X сообщение Y»
        for kw in ("напиши в макс", "напиши макс", "напиши сообщение", "отправь в макс"):
            if kw in text:
                rest = text[text.index(kw) + len(kw):].strip()
                break
        else:
            return "", ""

        # Разделитель — двоеточие.
        if ":" in rest:
            chat, msg = rest.split(":", 1)
            return chat.strip(), msg.strip()
        # Или «сообщение» как разделитель.
        if " сообщение " in rest:
            chat, msg = rest.split(" сообщение ", 1)
            return chat.strip(), msg.strip()
        # Только «кому» — что спросим отдельно.
        return rest.strip(), ""


__all__ = ["AgentMessenger"]
