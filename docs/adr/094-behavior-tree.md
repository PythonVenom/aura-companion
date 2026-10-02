# ADR-094: Behavior Tree Routing

**Дата:** 2026-10-02
**Статус:** Проект

## Контекст
37 агентов в flat-списке. При 200+ плагинов — 200 проверок.

## Решение
Behavior Tree с бинарными узлами: Control/Open/Search/Ask/Fallback.
Реализация через LangGraph.

## Ссылки
ADR-093 (Copilot), ADR-095 (Hands-Free)
