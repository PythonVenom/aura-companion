# ADR-080: Web UI (universal)

**Дата:** 2026-10-02
**Статус:** Принято

## Контекст
Нативный виджет на каждую DE = 13+ штук. Нужен универсальный UI.
Решение: одна HTML-страница через HTTP API (ADR-079).

## Решение
`aura/web/ui.html` — single-page, vanilla JS, без CDN.
- GET /ui — отдаёт HTML
- Chat: POST /chat + GET /chat/history
- Poll /status каждые 2 сек
- Работает offline, mobile-friendly

## Уникальность
- 100% DE сразу (браузер есть везде)
- 100% ОС сразу (Firefox/Chrome/Safari/Edge)
- PWA-ready (manifest позже)

## YAGNI
- Не React/Vue (избыточно)
- Не Tailwind (инлайн CSS)
- Нет auth (localhost, MVP)
- Нет WebSocket (poll 2 сек)

## Последствия
- Fallback для всех клиентов
- iPhone/Android через PWA
- SNI → может открыть Web UI
- Windows/Mac — то же

## Ссылки
ADR-042 (старый skeleton), ADR-079 (HTTP API), ADR-067 (Plasma widget)
