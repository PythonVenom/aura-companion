
# ADR-013: Dialogue Manager — сценарный диалог для мессенджеров

## Дата
2026-09-26

## Статус
Принято

## Контекст

ADR-012 ввёл плоский FSM (idle / awaiting_command / ask_text / ask_confirm). Он работает для **одношаговых** команд: «Аура, напиши Петруха привет» → ввод → подтверждение.

**Но он не покрывает сценарии из 5+ шагов:**
1. «Аура, открой макс».
2. «Найди чат Петруха».
3. «Напиши в чат».
4. «Привет, как дела».
5. «Отправить?» → «да».

Это **не одна команда**, это **диалог**. Пользователь ведёт Ауру по шагам, отвечает на её вопросы, подтверждает.

**Ключевая задача:** этот шаблон нужен для **всех мессенджеров** — Макс, Telegram, WhatsApp, Gmail, Яндекс.Почта. Один диалог-менеджер, разные исполнители.

## Решение

**Frame-based dialogue manager.** Термин из Jurafsky & Martin, «Speech and Language Processing», глава 24.

### Три подсистемы

1. **Dialogue State Tracker (DST)** — хранит: активный сценарий, текущий шаг, значения слотов.
2. **Dialogue Manager** — решает: вызвать агент / спросить слот / завершить.
3. **NLG** — формулирует вопросы: «Кому написать?», «Что написать?».

### Frame (сценарий)

Сценарий = **набор шагов** + **обязательные слоты**.

```python
@dataclass
class Scenario:
    name: str                    # "messenger_send"
    agent: str                   # "messenger"
    steps: list[str]             # ["open", "find_chat", "open_input", "send", "confirm"]
    required_slots: list[str]    # ["app", "chat", "text"]
    optional_slots: dict         # {"confirm": True}
```

### Слоты

- `app` — имя приложения («макс», «телеграм»).
- `chat` — имя чата («Петруха»).
- `text` — текст сообщения («привет»).
- `confirmed` — bool, отправлено ли подтверждение.

### Сценарии — registry

```python
SCENARIOS = {
    "messenger_send": Scenario(
        name="messenger_send",
        agent="messenger",
        steps=["open", "find_chat", "open_input", "send", "confirm"],
        required_slots=["app", "chat", "text"],
    ),
    # "telegram_send": ...  (будущее)
    # "email_send": ...     (будущее)
}
```

### Dialogue Manager — логика

```
process_command(cmd):
    1. Если сценарий активен:
        - Извлечь слоты из cmd.
        - Перейти к следующему шагу.
    2. Если сценарий не активен:
        - Найти сценарий по ключевым словам cmd.
        - Начать сценарий.
    3. Проверить, все ли required_slots заполнены:
        - Если да → выполнить шаги агента.
        - Если нет → спросить недостающий слот (NLG).
    4. После выполнения — подтверждение.
    5. Подтверждение «да» → финальный шаг (отправить).
    6. «Нет» / «отмена» → clear.
```

### Пример диалога

```
[IDLE]
Пользователь: «Аура, открой макс»
DM: Scenario=messenger_send, slots={app: макс}, step=open
    Вызов: messenger.open_max() → «Открыла Макс»
    Шаг: find_chat (нужен slot chat)

[SCENARIO_ACTIVE]
DM: «Какой чат?»
Пользователь: «Петруха»
DM: slots={app: макс, chat: Петруха}, step=find_chat
    Вызов: messenger.find_chat("Петруха") → «Открыла чат Петруха»
    Шаг: open_input

[SCENARIO_ACTIVE]
DM: «Что написать?»
Пользователь: «Привет, как дела»
DM: slots={...text: привет как дела}, step=send
    Вызов: messenger.send_message("Петруха", "привет как дела") → «Ввела текст»
    Шаг: confirm

[SCENARIO_ACTIVE]
DM: «Написала: привет как дела. Отправить?»
Пользователь: «Да»
DM: Вызов: messenger.finalize_send() → «Отправила»
    Сценарий завершён → IDLE

[IDLE]
```

### Где живёт

`aura/dialogue_manager.py` — модуль.

`aura_main.py` — интеграция:
- Заменяет `_handle_fsm`.
- В главном цикле: после активации или в `awaiting_command` — вызвать `dm.process(cmd, is_active_dialog=False/True)`.
- Если `dm.needs_response()` — задать вопрос.
- Если `dm.is_done()` — завершить.

### Что значит «без активации»

Когда сценарий активен — **не нужна** «Аура» на каждом шаге. Пользователь отвечает на вопросы DM как в обычном диалоге.

**Исключение:** «Аура» в любой момент → сброс сценария.

### Расширяемость для других мессенджеров

Каждый мессенджер реализует **AgentMessenger**-подобный интерфейс:

```python
class AgentTelegram(BaseAgent):
    def open_app(self): ...
    def find_chat(self, query): ...
    def open_input(self): ...
    def send_message(self, chat, text): ...
    def finalize_send(self): ...
    def clear_input(self): ...
```

Dialogue Manager работает с **любым** агентом, реализующим этот контракт.

## Обоснование

- **Frame-based dialogue** — стандарт в индустрии (Rasa, Dialogflow, Voiceflow).
- **Jurafsky & Martin** — глава 24.
- **Один менеджер, много агентов** — Open-Closed Principle (SOLID).
- **Слоты** — расширяемо. Новый мессенджер = новый сценарий + агент.
- **FSM переходит в DM** — не ломаем, а расширяем.

## Последствия

**Положительные:**
- Многошаговый диалог для всех мессенджеров.
- Шаблон для Telegram, WhatsApp, Gmail.
- Слоты явные — легко тестировать.
- NLG отделён от логики.

**Отрицательные:**
- Больше кода — `dialogue_manager.py` + тесты.
- Миграция: `_handle_fsm` уходит, DM приходит.
- Сложнее отлаживать (больше состояний).

**Риски:**
- Слот `chat` распознан неверно → не тот чат. Митигация: подтверждение перед отправкой.
- Пользователь говорит не по сценарию. Митигация: «Извини, не поняла. Отменить?».
- Долгий сценарий (5+ шагов). Митигация: таймаут 60 сек.

## Что НЕ делаем

- Не делаем **общий** dialogue manager для всех задач. Только **сценарии мессенджеров**.
- Не делаем NLU через LLM. Простые keywords + слоты.
- Не убираем ADR-012 — он работает для одного шага. DM — расширение.

## Реализация

1. `aura/dialogue_manager.py` — Scenario, DialogueManager.
2. `aura/scenarios/` — папка со сценариями (messenger_send.py, позже telegram_send.py).
3. `aura_main.py` — замена `_handle_fsm` на `dm.process()`.
4. Тесты: `test_dialogue_manager.py` — 10–12.
5. Живой прогон: полный сценарий Макса.

## Связь

- ADR-010 — DoD беты.
- ADR-011 — модульная архитектура.
- ADR-012 — Dialog FSM (основа).
- `docs/architecture.md` — архитектура.
- `docs/manifesto.md` — философия.

## Ссылки

- Jurafsky & Martin, «Speech and Language Processing», 3rd ed., глава 24.
- Rasa, «Forms and Slots», 2024.
- Fillmore, «Frame Semantics», 1976.
- Nygard, «Documenting Architecture Decisions», 2011.
