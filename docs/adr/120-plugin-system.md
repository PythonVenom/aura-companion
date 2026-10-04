# ADR-120: Plugin System

**Статус:** Accepted
**Дата:** 2026-10-02

## Решение

`aura/plugins/builtin/<name>/plugin.yaml` — handlers, routes, evals, i18n.
Loader сканирует, регистрирует. Ядро не трогаем при добавлении фичи.
