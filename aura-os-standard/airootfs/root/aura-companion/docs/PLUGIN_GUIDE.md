# Plugin Guide — как написать плагин для Aura

> Наука: Nielsen #10 (Help & Documentation), Write the Docs 2017.
> Философия: 100 строк кода → работающий агент.

---

## Что такое плагин

Плагин — это папка в ~/.local/share/aura/plugins/<id>/ с двумя файлами:

- manifest.json   — метаданные
- __init__.py     — код (наследник BaseAgent)

После установки агент автоматически регистрируется в orchestrator.

---

## Быстрый старт (5 минут)

### 1. Создай структуру

mkdir -p ~/.local/share/aura/plugins/my_plugin
cd ~/.local/share/aura/plugins/my_plugin

### 2. manifest.json

{
  "id": "my_plugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "author": "Твоё имя",
  "license": "MIT",
  "description": "Что делает",
  "tags": ["demo"],
  "requires": ["aura>=8.0"]
}

### 3. __init__.py

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentMyPlugin(BaseAgent):
    name = "my_plugin"
    TRIGGERS = ("тест плагин", "hello plugin")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse.ok(
            text=f"Плагин работает: {request.text}",
            agent_name=self.name,
        )

### 4. Перезапусти Aura

systemctl --user restart aura.service

### 5. Скажи

Аура, тест плагин

---

## API агента

### Обязательные атрибуты

- name — имя агента (snake_case)
- TRIGGERS или KEYWORDS — фразы для активации

### Обязательные методы

- can_handle(request) -> bool — получит ли агент запрос
- handle(request) -> AgentResponse — обработать запрос

### AgentRequest

- request.text — полный текст команды
- request.user — имя пользователя

### AgentResponse

- AgentResponse.ok(text="Ответ", agent_name=self.name)
- AgentResponse.not_handled(agent_name=self.name)

---

## Чего НЕ делать

- Не глотать исключения молча. Используй contextlib.suppress.
- Не блокировать event loop. Всё дольше 100мс — через asyncio.to_thread.
- Не хардкодить пути. Используй aura.paths.
- Не логировать секреты. Токены только в keyring.

---

## Чего ДЕЛАТЬ

- Один плагин = одна задача.
- Тесты обязательны. Минимум 5.
- Graceful degradation. Если зависимость недоступна — сообщи.
- Документируй TRIGGERS.

---

## Примеры в репо

- aura/agents/scenes.py — простой (сценарии)
- aura/agents/mqtt.py — средний (внешний сервис)
- aura/agents/planner.py — сложный (LLM + react_loop)

---

## Установка/удаление

from aura.core.plugin_manager import PluginManager
pm = PluginManager()
pm.install(source=Path("/path/to/my_plugin"))
for p in pm.list_plugins():
    print(p.id, p.version)
pm.remove("my_plugin")

---

## FAQ

Q: Как добавить свою зависимость?
A: pip install в venv Aura. Или requires в manifest.

Q: Как тестировать плагин?
A: pytest tests/test_my_plugin.py — пример в tests/test_scenes.py.

Q: Может ли плагин обращаться к другим агентам?
A: Да, через orchestrator. См. aura/agents/planner.py.

Q: Что если плагин падает?
A: Orchestrator ловит исключения, Aura не падает.

---

Написал плагин — отправь PR в github.com/PythonVenom/aura-companion.
