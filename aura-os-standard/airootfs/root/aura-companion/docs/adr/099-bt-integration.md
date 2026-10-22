# ADR-099: Behavior Tree Integration

**Дата:** 2026-10-02
**Статус:** Принято (MVP)

## Контекст
Orchestrator использует flat-scan по 41 агенту. O(n).
Нужно O(log n) через Behavior Tree (ADR-094).

## Решение
`aura/core/route_tree.py` — конкретная BT для Aura:
- Control? → aura_ctl
- Open? → Resolution Cascade (ADR-098)
- Ask? → LLM/агенты (fallback)

## Ссылки
ADR-094 (BT), ADR-098 (Cascade)
