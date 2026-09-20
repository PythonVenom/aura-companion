"""
Машинка Tabs: Управление вкладками Firefox (AgentBrowserTabs)
Через native messaging host + Unix socket.
"""

import os
import json
import socket
import struct
from agents.base import MicroAgent


SOCKET_PATH = "/tmp/aura_firefox.sock"


class AgentBrowserTabs(MicroAgent):
    def __init__(self):
        super().__init__("browser_tabs", "Управление вкладками Firefox")
        self.ready = False
        self._check()
        if self.ready:
            print("✅ BrowserTabs загружен (Firefox bridge)")
        else:
            print("⚠️ BrowserTabs: Firefox bridge не найден")

    def _check(self):
        """Проверить, что socket существует и отвечает"""
        if not os.path.exists(SOCKET_PATH):
            self.ready = False
            return
        try:
            result = self._send({"action": "ping"}, timeout=3)
            if result and result.get('pong'):
                self.ready = True
        except:
            self.ready = False

    def _send(self, msg, timeout=10):
        """Отправить команду host'у, получить ответ"""
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect(SOCKET_PATH)

            data = json.dumps(msg).encode('utf-8')
            sock.sendall(struct.pack('@I', len(data)) + data)

            raw_length = sock.recv(4)
            if len(raw_length) < 4:
                sock.close()
                return None
            length = struct.unpack('@I', raw_length)[0]
            response = sock.recv(length)
            sock.close()

            return json.loads(response.decode('utf-8'))
        except Exception as e:
            return {"error": str(e)}

    def list_tabs(self):
        """Список всех вкладок"""
        if not self.ready:
            return "❌ Firefox bridge не готов"

        result = self._send({"action": "list_tabs"})
        if not result or 'tabs' not in result:
            return f"❌ Ошибка: {result}"

        tabs = result['tabs']
        if not tabs:
            return "📭 Нет открытых вкладок"

        answer = f"🌐 Вкладок Firefox: {len(tabs)}\n\n"
        for t in tabs:
            active = " ← АКТИВНАЯ" if t['active'] else ""
            answer += f"[{t['id']}] {t['title'][:60]}{active}\n"

        return answer

    def find_tab(self, query):
        """Найти вкладку по имени"""
        if not self.ready:
            return "❌ Firefox bridge не готов"

        result = self._send({"action": "find_tab", "query": query})
        if not result or 'tabs' not in result:
            return f"❌ Ошибка"

        tabs = result['tabs']
        if not tabs:
            return f"❌ Вкладка '{query}' не найдена"

        answer = f"🔍 Найдено: {len(tabs)}\n\n"
        for t in tabs:
            answer += f"[{t['id']}] {t['title'][:60]}\n"

        return answer

    def focus_tab(self, query):
        """Переключиться на вкладку по имени"""
        if not self.ready:
            return "❌ Firefox bridge не готов"

        result = self._send({"action": "focus_tab_by_name", "query": query})
        if result.get('error'):
            return f"❌ Вкладка '{query}' не найдена"
        if result.get('success'):
            return f"✅ Переключилась на: {result.get('title', query)[:60]}"
        return f"❌ Ошибка: {result}"

    def close_tab(self, query):
        """Закрыть вкладку по имени"""
        if not self.ready:
            return "❌ Firefox bridge не готов"

        result = self._send({"action": "close_tab_by_name", "query": query})
        if result.get('error'):
            return f"❌ Вкладка '{query}' не найдена"
        if result.get('success'):
            return f"✅ Закрыла: {result.get('title', query)[:60]}"
        return f"❌ Ошибка: {result}"

    def open_tab(self, url):
        """Открыть новую вкладку"""
        if not self.ready:
            return "❌ Firefox bridge не готов"

        if not url.startswith('http'):
            url = 'https://' + url

        result = self._send({"action": "open_tab", "url": url})
        if result.get('error'):
            return f"❌ Ошибка: {result['error']}"
        return f"✅ Открыла: {url[:60]}"

    def search(self, query):
        """Открыть новую вкладку с поиском"""
        if not self.ready:
            return "❌ Firefox bridge не готов"

        result = self._send({"action": "new_tab_search", "query": query})
        if result.get('error'):
            return f"❌ Ошибка: {result['error']}"
        return f"✅ Ищу: {query}"

    def next_tab(self):
        """Следующая вкладка"""
        if not self.ready:
            return "❌ Firefox bridge не готов"
        result = self._send({"action": "next_tab"})
        if result.get('success'):
            return f"▶️ Следующая: {result.get('title', '')[:60]}"
        return f"❌ Ошибка"

    def prev_tab(self):
        """Предыдущая вкладка"""
        if not self.ready:
            return "❌ Firefox bridge не готов"
        result = self._send({"action": "prev_tab"})
        if result.get('success'):
            return f"◀️ Предыдущая: {result.get('title', '')[:60]}"
        return f"❌ Ошибка"

    def execute(self, command):
        cmd = command.lower().strip()

        if 'список вкладок' in cmd or 'какие вкладки' in cmd or 'что открыто в браузере' in cmd:
            return self.list_tabs()

        if 'найди вкладку' in cmd:
            query = cmd.replace('найди вкладку', '').strip()
            return self.find_tab(query)

        if 'переключись на вкладку' in cmd or 'открой вкладку' in cmd:
            query = cmd.replace('переключись на вкладку', '').replace('открой вкладку', '').strip()
            return self.focus_tab(query)

        if 'закрой вкладку' in cmd:
            query = cmd.replace('закрой вкладку', '').strip()
            return self.close_tab(query)

        if 'следующая вкладка' in cmd:
            return self.next_tab()

        if 'предыдущая вкладка' in cmd:
            return self.prev_tab()

        return "🌐 BrowserTabs готов. Команды: список вкладок, переключись на вкладку X, закрой вкладку X"
