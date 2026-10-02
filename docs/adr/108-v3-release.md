# ADR-108: v3.0 — Release

**Статус:** Accepted
**Дата:** 2026-10-02

## Что вошло в v3.0

- `paths.py` во всех агентах (ADR-106)
- `RouteTree` расширен (7 листьев) и интегрирован в Orchestrator (ADR-107)
- 22 capability handlers в `dispatcher`
- Bridge работает (socket `/tmp/aura_firefox.sock`)
- `vk_navigate` матчит и по имени секции, и по URL-слагу (`im/audio/friends`)

## Интеграция

Порядок в `Orchestrator.process(text)`:

1. `registry.find()` — агенты
2. `route_tree.handle()` → `dispatcher.dispatch(cap, args)` — быстрый regex
3. `tool_router.route()` — LLM tool calling
4. `brain.ask()` — LLM fallback
5. `fallback_text`

## Метрики

- ADR: 87 (включая 108)
- Tests: 1332 passed (заморожены)
- Handlers: 22
- RouteTree leaves: 7 (control/power/music/time/browser/app/ask)

## Что уехало в v3.1

- VM/virt-manager (делегировано, батя тестит на Mint)
- vk.* команды в RouteTree
- Авто-reload расширения

## Решение

Тег `v3.0`. v3.1 — стабилизация и расширение.
