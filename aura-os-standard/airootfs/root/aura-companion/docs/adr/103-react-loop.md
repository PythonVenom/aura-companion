# ADR-103: ReAct Loop

**Дата:** 2026-10-02
**Статус:** Принято (MVP)

## Контекст
HTN Planner (ADR-102) даёт список операторов.
Но не выполняет их и не проверяет результат — нужен цикл.

## Решение
`aura/core/react_loop.py`:
- Step: iteration, operator, args, result, ok, error
- Episode: goal, steps, done, reason
- ReActLoop: executor + reflector, MAX=3 итерации
- format_episode() — текст для голоса

Агент `react_agent` — «выполни план X».

MVP: mock executor (без реального действия).
Реальный dispatch к capability handlers — следующая итерация.

## YAGNI
- Не LLM-рефлексия (эвристика: все ok → done)
- Не сохраняем episode в Logbook (позже)

## Ссылки
ADR-102 (HTN), ADR-104 (Capability dispatch, план)
