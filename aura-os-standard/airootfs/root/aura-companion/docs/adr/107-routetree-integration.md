# ADR-107: RouteTree Integration

**Дата:** 2026-10-02
**Статус:** Принято (MVP)

## Контекст
RouteTree (ADR-094) реализован, но не подключён к orchestrator.
Flat-scan по 44 агентам. O(n).

## Решение
В `Orchestrator.process()` добавлен вызов `build_route_tree().handle()`.
Пока — только для логирования (route hint), поведение не меняется.

## План
- v3.1: route=control → прямо в aura_ctl минуя registry
- v3.1: route=open → прямо в AgentOpenResolver
- v3.1: route=ask → registry.find (как сейчас)

## Ссылки
ADR-094 (BT), ADR-099 (BT Integration), ADR-105 (Bridge)
