# ADR-042: Web UI (htmx)

**Дата:** 2026-09-28
**Статус:** Проект
**Связано:** ADR-029 (Multi-client), ADR-032 (JSON-RPC)

## Контекст

Клиенты: CLI (есть), KDE widget (есть), Android (Q2 2026), TG bot (Q1 2026).
Web UI нужен для:
- Удалённой отладки (тот же LAN)
- Скринридера на чужом ПК (accessibility)
- Демонстрации без установки

## Решение

**htmx + FastAPI** — минималистичный Web UI.

### Почему htmx (не React)

| Критерий | htmx | React |
|---|---|---|
| npm | не нужен | нужен |
| Bundle | ~15 КБ | ~150 КБ |
| Компоненты | HTML + атрибуты | JSX |
| Кривая | низкая | средняя |
| Тесты | pytest + httpx | vitest + playwright |

**YAGNI:** нам нужен чат + статус + настройки, не SPA.

### Стек

- **Backend:** FastAPI (async, JSON-RPC bridge)
- **Frontend:** htmx + Jinja2 (HTML-шаблоны)
- **Auth:** JWT (та же схема, ADR-032)
- **WS:** WebSocket для voice.stream

### Страницы (MVP)

- `/` — чат (voice + text)
- `/status` — агенты, service, doctor
- `/settings` — persona, voice_profile
- `/wrappers` — список, статус
- `/adr` — список ADR (для документации)

### Деплой

- `systemd --user aura-web.service`
- Порт 8080 (LAN) или через WireGuard (WAN)
- Reverse-proxy Caddy (опционально, для HTTPS)

### Что НЕ делаем

- SPA (overkill)
- Server-side rendering тяжёлых таблиц (htmx справится)
- Отдельная БД (settings.json + JSON-RPC к ядру)

## Последствия

**Плюсы:** 1 файл, без npm, быстро
**Минусы:** htmx менее популярен (но паттерн проще)

## Связанные
- ADR-029 (Multi-client)
- ADR-032 (JSON-RPC)
