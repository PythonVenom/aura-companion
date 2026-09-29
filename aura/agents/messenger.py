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
import time

from aura.core.bridge import send_command, error_text
from aura.dialog_fsm import set_state as fsm_set
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


# --- Bug 13: помним свои отправленные сообщения ---
_sent_recent: list = []   # [(chat, text, ts)]
_SENT_TTL = 300.0         # 5 минут


def _remember_sent(chat: str, text: str) -> None:
    """Запомнить: мы только что отправили text в chat."""
    if not chat or not text:
        return
    _sent_recent.append((chat, text.strip(), time.time()))
    cutoff = time.time() - _SENT_TTL
    _sent_recent[:] = [x for x in _sent_recent if x[2] > cutoff]


def is_own_message(chat: str, preview: str) -> bool:
    """True если preview — наше недавнее сообщение (Bug 13).

    MAX не всегда добавляет «Вы:», поэтому проверяем по совпадению
    с недавно отправленным текстом.
    """
    if not preview or not chat:
        return False
    p = preview.strip().lower()
    for c, t, ts in _sent_recent:
        if time.time() - ts > _SENT_TTL:
            continue
        if c != chat:
            continue
        if t and t.lower() in p:
            return True
    return False


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
    platform = "max"  # Bug 51: "max" или "wa"
    _last_platform = "max"  # Bug 52: sticky (запоминаем последнюю)

    OPEN_KEYWORDS = (
        "открой макс", "открыть макс", "макс веб",
        "открой вотсап", "открыть вотсап", "открой ватсап",
        "открыть ватсап", "открой whatsapp", "вотсап веб",
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
        "напиши в чат",   # «напиши в чат Петруха» — открыть + спросить текст
        "напиши чат",
    )
    READ_KEYWORDS = (
        "что написали",
        "прочитай макс",
        "прочитай чат",
        "новые сообщения",
    )
    SEND_KEYWORDS = (
        "напиши в макс", "напиши макс",
        "напиши сообщение", "напиши сообщ",
        "напиши смс",
        # Bug 53: WhatsApp-варианты
        "напиши в вотсап", "напиши вотсап", "напиши ватсап",
        "напиши в ватсап", "напиши whatsapp",
    )
    FINALIZE_KEYWORDS = ("отправь", "отправить", "давай отправим", "отправляй")
    CLEAR_KEYWORDS = ("отмени", "отмена", "очисти", "удали текст")
    # Только ошибочные формы T-one. «макс», «максе» — правильные.
    MAX_ALIASES = ("макте", "макт", "мактэ", "макст", "максу", "макса", "максы", "максэ", "максом")
    WA_ALIASES = ("вотсап", "ватсап", "вотсапе", "ватсапе", "whatsapp",
                  "вацап", "вотс", "вотцап", "вотсаппе")

    def _detect_platform(self, text: str) -> None:
        """Bug 51+52: платформа по тексту ИЛИ sticky (последняя)."""
        t = text.lower()
        wa_kw = ("вотсап", "ватсап", "whatsapp", "вацап", "вотцап",
                 "вотсапп", "вотс")
        if any(kw in t for kw in wa_kw):
            self.platform = "wa"
            AgentMessenger._last_platform = "wa"
            return
        if "макс" in t or "max" in t:
            self.platform = "max"
            AgentMessenger._last_platform = "max"
            return
        # Bug 52: sticky — если в тексте нет указателя, берём последнюю
        self.platform = AgentMessenger._last_platform

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
            + self.FINALIZE_KEYWORDS + self.CLEAR_KEYWORDS
        )
        # Bug 53: WA-слова (вотсап/ватсап/whatsapp/вацап)
        wa_kw = ("вотсап", "ватсап", "whatsapp", "вацап", "вотцап",
                 "вотсапп", "вотс")
        has_wa = any(kw in text for kw in wa_kw)
        if "макс" in text and any(kw in text for kw in all_kw):
            return True
        if has_wa and any(kw in text for kw in all_kw):
            return True
        if "чат" in text and any(kw in text for kw in self.FIND_KEYWORDS + self.READ_KEYWORDS):
            return True
        # «Напиши X: Y» или «Напиши сообщение X Y» — без «макс».
        if "напиши" in text and ("сообщение" in text or ":" in text):
            return True
        # Bug 54: «отправь/отмени» — ловим без указателя платформы
        # (sticky platform работает из предыдущего шага)
        if any(kw in text for kw in self.FINALIZE_KEYWORDS):
            return True
        if any(kw in text for kw in self.CLEAR_KEYWORDS):
            return True
        # «Напиши X Y» — без «макс», без «сообщение», но с двумя словами.
        # НЕ перехватываем: «напиши код», «напиши стих», «напиши письмо».
        if "напиши" in text:
            brain_words = ("код", "стих", "истори", "рассказ",
                           "письмо", "текст", "анекдот", "шутк",
                           "песн", "сказк", "программ")
            if not any(w in text for w in brain_words):
                after = text.split("напиши", 1)[1].strip().split()
                if len(after) >= 2:
                    return True
        return False

    async def handle(self, request: AgentRequest) -> AgentResponse:
        self._detect_platform(request.text)
        text = self._normalize(request.text.lower())

        # 1. Открыть Макс — фокус на вкладку.
        if any(kw in text for kw in self.OPEN_KEYWORDS):
            return AgentResponse.ok(self.open_max(), self.name)

        # 2. Список чатов.
        if any(kw in text for kw in self.LIST_KEYWORDS):
            return AgentResponse.ok(self.list_chats(), self.name)

        # 3. Найти чат / написать в чат.
        if any(kw in text for kw in self.FIND_KEYWORDS):
            query = self._extract_chat_name(text)
            if not query:
                return AgentResponse.ok("Какой чат?", self.name)
            result = self.find_chat(query)
            # Если «напиши в чат X» — открыли чат, спрашиваем текст.
            if "напиши" in text and "не найден" not in result:
                fsm_set("ask_text", chat=query)
                return AgentResponse.ok(result + " Что написать?", self.name, fsm_state="ask_text", chat=query)
            return AgentResponse.ok(result, self.name)

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
            fsm_set("ask_confirm", chat=chat, text=msg)
            return AgentResponse.ok(self.send_message(chat, msg), self.name, fsm_state="ask_confirm", chat=chat)

        # 6. Отправка / отмена введённого.
        if any(kw in text for kw in self.FINALIZE_KEYWORDS):
            fsm_set("idle")
            return AgentResponse.ok(self.finalize_send(), self.name, fsm_state="idle")
        if any(kw in text for kw in self.CLEAR_KEYWORDS):
            fsm_set("idle")
            return AgentResponse.ok(self.clear_input(), self.name, fsm_state="idle")

        return AgentResponse.not_handled(self.name)

    # --- Команды ---

    def open_max(self) -> str:
        """Bug 54: сначала искать открытую вкладку → фокус, потом открывать."""
        # 1. Искать существующую вкладку
        needle = "whatsapp" if self.platform == "wa" else "max.ru"
        tabs = send_command({"action": "list_tabs"})
        if tabs and "tabs" in tabs:
            for t in tabs["tabs"]:
                url = (t.get("url") or "").lower()
                if needle in url:
                    r = send_command({"action": "activate_tab", "tab_id": t["id"]})
                    if r and r.get("success"):
                        name = "WhatsApp" if self.platform == "wa" else "Макс"
                        return f"🌐 Фокус на {name}"

        # 2. Не нашли — открыть новую
        url = ("https://web.whatsapp.com" if self.platform == "wa"
               else "https://web.max.ru")
        result = send_command({"action": "open_tab", "url": url, "active": True})
        if result is None or "error" in result:
            return error_text(result)
        name = "WhatsApp" if self.platform == "wa" else "Макс"
        return f"🌐 Открыла {name}"

    def list_chats(self) -> str:
        result = send_command({"action": f"{self.platform}_list_chats"})
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

    def get_last_message_preview(self) -> dict:
        """Вернуть {chat, preview} первого (свежего) чата."""
        result = send_command({"action": f"{self.platform}_list_chats"})
        if result is None or "error" in result:
            return {}
        chats = result.get("data", {}).get("chats", [])
        if not chats:
            return {}
        first = chats[0]
        return {"chat": first.get("name", ""), "preview": first.get("preview", "")}

    def get_all_previews(self) -> list:
        """Вернуть [{chat, preview}, ...] для всех чатов (Bug 2)."""
        result = send_command({"action": f"{self.platform}_list_chats"})
        if result is None or "error" in result:
            return []
        chats = result.get("data", {}).get("chats", [])
        out = []
        for c in chats:
            name = c.get("name", "")
            preview = c.get("preview", "")
            if name and preview:
                out.append({"chat": name, "preview": preview})
        return out

    def get_title(self) -> dict:
        """Вернуть {title, url} активной вкладки Макса."""
        result = send_command({"action": f"{self.platform}_title"})
        if result is None or "error" in result:
            return {}
        return result.get("data", {})

    def find_chat(self, query: str) -> str:
        # Bug 37: НЕ поднимаем Firefox принудительно.
        result = send_command({"action": f"{self.platform}_find_chat", "query": query})
        if result is None or "error" in result:
            return error_text(result)
        data = result.get("data", {})
        if not data.get("found"):
            return f"🌐 Чат «{query}» не найден"

        # Bug 57: verify-after-action — проверяем что чат РЕАЛЬНО открылся.
        import time
        time.sleep(0.8)  # ждём перерисовки UI
        title_r = send_command({"action": f"{self.platform}_title"})
        cur_title = ""
        if title_r and title_r.get("ok"):
            cur_title = (title_r.get("data", {}).get("title") or "").strip()

        found_name = (data.get("name") or query).strip()
        q_low = query.lower().strip()
        t_low = cur_title.lower()

        # Совпадение: query или found_name в title (или наоборот)
        ok = (
            (q_low and q_low in t_low) or
            (t_low and t_low in q_low) or
            (found_name.lower() in t_low) or
            (t_low and t_low in found_name.lower())
        )
        if ok:
            return f"🌐 Открыла чат: {cur_title[:60]}"
        # Не открылся — честный fail
        return f"🌐 Клик по «{query}» не сработал (title: {cur_title[:40]!r})"

    def read_last(self) -> str:
        result = send_command({"action": f"{self.platform}_read_last"})
        if result is None or "error" in result:
            return error_text(result)
        data = result.get("data", {})
        last = data.get("last", "")
        if not last:
            return "🌐 Нет новых сообщений"
        return f"🌐 Последнее сообщение: {last[:200]}"

    @staticmethod
    def _focus_firefox() -> None:
        """Поднять окно Firefox (для зрительной фиксации)."""
        import subprocess
        try:
            subprocess.run(
                ["wmctrl", "-a", "firefox"],
                check=False, timeout=2,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    def send_message(self, chat: str, message: str) -> str:
        """Открыть чат, ввести текст (без отправки)."""
        # Bug 55: если чат УЖЕ открыт (title совпадает) — не искать повторно.
        title_r = send_command({"action": f"{self.platform}_title"})
        already_open = False
        if title_r and title_r.get("ok"):
            cur = (title_r.get("data", {}).get("title") or "").lower().strip()
            if cur and (chat.lower().strip() in cur or cur in chat.lower().strip()):
                already_open = True

        if not already_open:
            find = send_command({"action": f"{self.platform}_find_chat", "query": chat})
            if find is None or "error" in find:
                return error_text(find)
            data = find.get("data", {})
            if not data.get("found"):
                return f"🌐 Чат «{chat}» не найден"

        # 2. Ввести текст.
        send = send_command({"action": f"{self.platform}_send_message", "text": message})
        if send is None or "error" in send:
            return error_text(send)
        sd = send.get("data", {})
        if sd.get("typed"):
            _remember_sent(chat, message)   # Bug 13
            return f"🌐 Ввела текст в чат «{chat}»"
        return "🌐 Не удалось ввести текст"

    def finalize_send(self) -> str:
        """Отправить введённое сообщение (нажать Enter)."""
        result = send_command({"action": f"{self.platform}_send_finalize"})
        if result is None or "error" in result:
            return error_text(result)
        data = result.get("data", {})
        if data.get("sent"):
            return "🌐 Отправила сообщение"
        return f"🌐 Не удалось отправить: {data.get('error', 'unknown')}"

    def clear_input(self) -> str:
        """Очистить поле ввода в Максе."""
        result = send_command({"action": f"{self.platform}_clear_input"})
        if result is None or "error" in result:
            return error_text(result)
        return "🌐 Очистила поле ввода"

    # --- Разбор аргументов ---

    # Bug 61: стоп-слова — где заканчивается имя чата
    CHAT_STOP = (" и напиши", " и отправь", " или ", " а потом", " потом ",
                 " затем ", " напиши ", " напиши,", " отправь", " сообщение",
                 " и ", " а ", " с текстом", " текст ", ", напиши")

    @staticmethod
    def _extract_chat_name(text: str) -> str:
        for kw in ("найди чат с", "найди чат", "открой чат с", "открой чат",
                   "перейди в чат с", "перейди в чат"):
            if kw in text:
                idx = text.index(kw) + len(kw)
                rest = text[idx:].strip().strip(".,!?")
                if not rest:
                    continue
                # Обрезаем по стоп-словам
                for stop in AgentMessenger.CHAT_STOP:
                    if stop in rest:
                        rest = rest.split(stop, 1)[0].strip()
                # Убираем хвостовые предлоги
                rest = rest.strip(" .,!?")
                if rest:
                    return rest
        return ""

    @staticmethod
    def _extract_send(text: str) -> tuple[str, str]:
        """Извлечь (кому, что) из «напиши маме: сегодня...»."""
        # Формат: «напиши X: Y» или «напиши X сообщение Y»
        for kw in ("напиши в макс", "напиши макс", "напиши сообщение", "отправь в макс",
                   "напиши в вотсап", "напиши вотсап", "напиши ватсап",
                   "напиши в ватсап", "напиши whatsapp"):
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
        # Без разделителя: первое слово = имя, остальное = текст.
        parts = rest.split(None, 1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        # Только одно слово — что спросим отдельно.
        return rest.strip(), ""


__all__ = ["AgentMessenger"]
