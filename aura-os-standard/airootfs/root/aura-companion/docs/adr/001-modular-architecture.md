# ADR-001: Модульная архитектура Ауры

## Дата
2026-09-20

## Статус
Принято

## Контекст
Монолит `aura_core.py` (80 агентов) привёл к:
- Двойному роутингу (ToolRouter + if/elif)
- Хардкоду путей
- Невозможности тестировать
- `import __main__` в агентах

14 сентября 2026 создан прототип правильной архитектуры:
- `aura/core/protocol.py` — AgentRequest/AgentResponse/AgentProtocol
- `aura/agents/time.py` — эталонный агент
- `aura/platform/base.py` — PlatformAdapter (Protocol)
- `tests/test_time.py` — 38 тестов

## Решение
Развивать модульную архитектуру `aura/`.

## Обоснование
- Protocol вместо наследования (PEP 544)
- Pydantic для валидации
- async/await для I/O
- pytest для каждого агента
- ADR для каждого решения

## Последствия
+ Изоляция агентов
+ Тестируемость
+ Кроссплатформенность
- Миграция 80 агентов
- Время на рефакторинг

## Ссылки
- PEP 544 — Protocols
- Pydantic
- pytest-asyncio
