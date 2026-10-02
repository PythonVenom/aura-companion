# ADR-102: HTN Planner

**Дата:** 2026-10-02
**Статус:** Принято (MVP)

## Контекст
Capability Graph (ADR-101) знает что умеет Aura.
Но не знает **как** достичь цели — нет декомпозиции.

## Решение
`aura/core/htn_planner.py`:
- Operator: capability + args + description
- Method: name + triggers + steps
- Planner: add_method, find_method, plan(goal)

MVP: 4 метода (open_target, system_check, morning_briefing,
focus_session). Без LLM — просто триггеры.

Агент `planner` — «как сделать X» → голосовой план.

## YAGNI
- Не LLM-декомпозиция (позже — ReAct ADR-103)
- Не планы на 20 шагов (MVP = 2-3 шага)

## Ссылки
ADR-101 (Capability Graph), ADR-103 (ReAct, план)
