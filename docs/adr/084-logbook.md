# ADR-084: Logbook

**Дата:** 2026-10-02
**Статус:** Принято

## Контекст

Aura работает, но нет контекста:
- Что делали вчера?
- Почему выбрали HTTP API, а не WebSocket?
- Где остановились?
- Какой день был?

Без Logbook: Care, Multi-AI, Smart Cleanup, Email — все слепые.

## Решение

`aura/core/logbook.py` — структурированный дневник.
- Формат: ~/.cache/aura/logbook/YYYY-MM-DD.jsonl (машинный)
- Человекочитаемый: YYYY-MM-DD.md
- Типы: event, decision, unresolved, mood
- CLI: aura_log (event/decision/unresolved/mood/today/search)

## YAGNI

- Нет SQLite (JSONL достаточно, index.db — позже)
- Нет поиска по embeddings (grep по meta хватает)
- Нет UI (markdown + CLI)

## ToC

Logbook = база для всех Extension (Care, Multi-AI, Email, Cleanup).

## Последствия

- Care Coordinator использует logbook для брифинга
- Multi-AI пишет в logbook что делали
- Smart Cleanup читает что использовалось
- Email Secretary помнит про что писали

## Ссылки
ADR-085 (Care), ADR-086 (Email), ADR-088 (Multi-AI), ADR-087 (Cleanup)
