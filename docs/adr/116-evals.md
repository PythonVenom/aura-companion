# ADR-116: Evals v0

**Статус:** Accepted
**Дата:** 2026-10-02

## Решение

Golden dataset — `evals/golden.yaml`, 50 запросов. Формат:
`input -> route + action + args`.

Прогон: `scripts/run_evals.py`. Метрика: pass %.

В CI: прогон перед каждым тегом (release gate).

## Последствия

- (+) замена промпта / RouteTree = измеряемо
- (+) регрессии ловятся на уровне intent, не кода
- (−) 50 мало, цель v4.0-beta: 200
