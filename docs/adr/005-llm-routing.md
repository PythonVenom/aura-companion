# ADR-005: LLM-роутинг в модульной архитектуре

## Дата
2026-09-20

## Статус
Принято

## Контекст

После Фазы 4.A (18 из 21 живого агента в модуле) остались два:
`brain` (LLM-фолбэк) и `tool_router` (LLM-роутинг с tool-calling).
Оба — часть Фазы 3 по migration-roadmap.md.

В монолите `AuraCore.process()` устроен так:

1. `tool_router.route(text)` — LLM выбирает инструмент.
2. Если не сработало — `brain.execute(text)` — LLM болтает.

Реестр `can_handle`/`handle` в модуле заменил `tool_router` —
но только частично. `can_handle` — regex/keywords, `tool_router` —
LLM с tool-calling.

Проверено: Ollama с `qwen2.5:7b-instruct-q4_K_M` поддерживает
`capabilities: [\"completion\", \"tools\"]`. Tool-calling работает.

## Решение

### Архитектура роутинга — три уровня

```
process(text):
    1. registry.find(request)     ← быстрый, детерминированный
       если агент найден → handle → вернуть
    2. tool_router.route(text)    ← LLM с tool-calling
       если tool или text → вернуть
    3. brain.ask(text)            ← LLM-болтовня
       вернуть
```

Отличие от монолита: монолит ставит `tool_router` первым.
Модуль ставит `registry` первым.


## Обоснование

1. Скорость. 95% команд — структурные. Реестр — мгновенно.
   LLM — 1–3 секунды. Для частых команд — реестр.
2. Стоимость. qwen2.5:7b на CPU — 100% загрузки на 2–3 секунды.
   На каждую команду — неприемлемо.
3. Надёжность. Реестр — детерминированный. LLM — вероятностный.
   Для критичных действий (power) — реестр.
4. Совместимость. Принцип 7 roadmap: никаких if/elif в process().
   Только реестр. LLM — дополнительный путь, не замена.

### Форма миграции

tool_router и brain — не BaseAgent. Они не обрабатывают команды
по keywords. Это сервисы, которые дёргает Orchestrator.

- aura/agents/brain.py — AgentBrain с ask(question) -> str.
- aura/agents/tool_router.py — AgentToolRouter с route(text) -> dict.
- Оба не наследуют BaseAgent. Не регистрируются в registry.

### Интеграция в Orchestrator

Orchestrator.__init__ принимает опциональные сервисы:

class Orchestrator:
    def __init__(self, tool_router=None, brain=None):
        self.registry = AgentRegistry()
        self.tool_router = tool_router
        self.brain = brain
        self.fallback_text = "Не расслышала, Создатель, повторите"

В process(): сначала registry.find, потом tool_router.route,
потом brain.ask. Через asyncio.to_thread (route и ask синхронные).

### Регистрация инструментов

В монолите — ~46 инструментов руками через register(...).
В модуле — тоже руками в bootstrap.py. Каждый инструмент —
обёртка над агентом.

Это техдолг. Идеально — автоматическая регистрация.
Требует, чтобы BaseAgent имел метаданные (описание, параметры).
Отдельная задача.

### Обработка ошибок

- LLM недоступен → route/ask возвращают ошибку. Orchestrator печатает предупреждение, идёт дальше.
- LLM вернул мусор → используется как есть.
- Всё упало → fallback_text.

## Последствия

### Положительные

- Модуль полностью воспроизводит AuraCore.process().
- LLM-роутинг работает для сложных фраз.
- Реестр остаётся быстрым для частых команд.
- Не блокирует: если LLM не нужен — None.
- Тестируемо: tool_router и brain можно мокать.

### Отрицательные

- Двойная регистрация инструментов.
- Синхронные сервисы в async-контексте.
- Порядок отличается от монолита.
- Зависимость от Ollama.

### Риски

- LLM может галлюцинировать. Митигация: system prompt с запретами.
- Реестр может перехватить. Митигация: узкие keywords.

## Что НЕ делаем

- Не мигрируем upgrader — мёртв (ADR-004).
- Не чиним гонку speaker.is_speaking — отдельная задача.
- Не делаем автоматическую регистрацию — отдельная задача.

## Проверка

1. pytest tests/test_brain.py tests/test_tool_router.py — зелёные.
2. Ручной прогон:
   - который час → AgentTime (реестр, мгновенно).
   - расскажи историю про космос → brain (LLM, 2–3 сек).
   - включи музыку → tool_router (LLM выбирает play_music).

## Ссылки
- ADR-001 — модульная архитектура
- ADR-003 — паритет aura_main.py
- ADR-004 — ревизия мёртвого кода
- docs/migration-roadmap.md — Фаза 3
- Ollama tool-calling API
