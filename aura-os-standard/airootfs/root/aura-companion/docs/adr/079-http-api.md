# ADR-079: HTTP API (DE-agnostic)

**Дата:** 2026-10-02
**Статус:** Принято

## Контекст

Aura привязана к Plasma widget. Нужно работать во всех DE (13) и ОС (6).
Решение — HTTP API как точка интеграции.

Существующий `aura/web/app.py` (ADR-042) — HTML + htmx skeleton, порт 8080.
Новый `aura/web/api.py` — чистый JSON API, порт 8765, для всех клиентов.
Дубль допустим: старый для debug, новый для integration.

## Решение

FastAPI + uvicorn на localhost:8765.

Endpoints (MVP):
- GET  /health         — health check (без auth)
- GET  /version        — версия Aura
- GET  /status         — состояние (state, text, version)
- GET  /agents         — список агентов
- GET  /chat/history   — история чата (JSONL, limit=100)
- POST /chat           — отправить сообщение (sync + inbox)

Клиенты: Web UI, SNI (pystray), GNOME Extension, Cinnamon Spice, Win tray,
Mac bar, PWA (iPhone/Android) — все через этот API.

## YAGNI

- Auth — позже (сначала localhost only)
- TLS — позже (ADR для production)
- WebSocket — позже (real-time push)
- gRPC — не нужно

## ToC

Узкое место — DE-agnostic. HTTP API его снимает.

## Последствия

- DE-agnostic: любой клиент на любом языке
- Web UI становится тривиальным (fetch /chat)
- LAN sync возможен (future)
- Старый `aura/web/app.py` (ADR-042) остаётся для debug

## Ссылки

- ADR-042 (Web UI skeleton)
- ADR-067 (Widget Control Panel)
- ADR-078 (Universal Installer)
- ADR-080 (SNI, план)
