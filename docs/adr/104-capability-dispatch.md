# ADR-104: Capability Dispatcher

**Дата:** 2026-10-02
**Статус:** Принято (MVP)

## Контекст
ReAct Loop (ADR-103) имеет mock executor.
Нужен реальный dispatch: capability name → handler.

## Решение
`aura/core/dispatcher.py`:
- register(capability, handler)
- dispatch(capability, args) → (ok, result)
- Defaults: world.state, context.recent

ReAct использует dispatcher как executor.
Handler может быть любым callable(args) → str.

## YAGNI
- Не async (sync достаточно)
- Не приоритеты (один handler = одна capability)
- Не ретраи (позже — в ReAct)

## Ссылки
ADR-101 (Graph), ADR-102 (HTN), ADR-103 (ReAct)
