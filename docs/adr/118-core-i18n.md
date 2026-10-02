# ADR-118: Core i18n

**Статус:** Accepted
**Дата:** 2026-10-02

## Решение

`aura/i18n/` — YAML, `t(key, **kw)`, `set_lang(code)`.
ru (native), en, zh, es. Арабский — v5 (RTL).
Все user-facing строки — через `t()`. LLM-промпты — тоже.
