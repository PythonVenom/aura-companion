# ADR-112: Observability (structured logs + traces)

**Статус:** Accepted
**Дата:** 2026-10-02

## Контекст

Сейчас в коде `print(f"⚠️ ...")`. Без структурированных логов
нельзя дебажить, измерять latency, находить регрессии.

## Решение

Модуль `aura/observability/`:
- `log(event, **fields)` — JSONL в `~/.cache/aura/logs.jsonl`
- `new_trace(name)` / `new_span(name)` — correlation id
- `tail(n)` — читать последние записи

Интеграция: orchestrator.process() → `new_trace`, каждая ветка → `log("route", ...)`.

## Последствия

- (+) можно мерить p50/p95 latency по event
- (+) видно, какой route сработал
- (+) дебаг по trace_id
- (−) +модуль, +файл логов (ротация — v5)
