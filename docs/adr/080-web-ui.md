# ADR-080: Web UI (universal)

**Дата:** 2026-10-02
**Статус:** Принято

## Контекст

Aura работает на многих DE/ОС. Нативный виджет на каждую DE = 13+ штук.
Решение: одна HTML-страница через HTTP API (ADR-079).

## Решение

Одна страница `aura/web/ui.html`, отдаётся через `GET /ui`.
- Чистый HTML + vanilla JS (без фреймворков, без CDN)
- Работает в любом браузере: Firefox, Chrome, Safari, Edge
- Работает offline (без внешних зависимостей)
- Mobile-friendly (viewport, media queries)
- Poll /status каждые 2 сек
- Chat: POST /chat + GET /chat/history

## Уникальность

- 100% DE сразу
- 100% ОС сразу
- Ноль установки для user (открыл браузер)
- PWA-ready (можно добавить manifest позже)

## YAGNI

- Не используем React/Vue (избыточно для 1 страницы)
- Не используем Tailwind (инлайн CSS)
- Нет авторизации (localhost only, MVP)
- Нет WebSocket (poll 2 сек достаточно)

## Последствия

- Все клиенты могут использовать этот UI как fallback
- iPhone/Android через браузер = PWA
- SNI (pystray) → можно открыть Web UI
- Windows/Mac — то же

## Ссылки

- ADR-079 (HTTP API)
- ADR-042 (Web UI skeleton — старый, htmx)
- ADR-067 (Widget Plasma — нативный)
