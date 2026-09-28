# ADR-041: Telegram Bot Client

**Дата:** 2026-09-28
**Статус:** Проект
**Связано:** ADR-029 (Multi-client), ADR-032 (JSON-RPC)

## Контекст

Telegram = 900M MAU, популярен в РФ/CIS. Люди привыкли писать боту.

Нужен **первый мобильный клиент** без Android-разработки.

## Решение

**Aura Bot** — Telegram-бот, тонкий клиент к ядру через JSON-RPC.

### Архитектура

    [Telegram Cloud] ⇄ [Bot (Python, aiogram)] ⇄ [Aura Core JSON-RPC]

Bot = bridge. Не хранит данные. Не имеет LLM. Всё — в ядре.

### Команды (mirror CLI)

- `/start` — привет + pairing (QR)
- `/voice <текст>` — голосовая команда → ядру
- `/timer 5m чай`
- `/reminder вода 60`
- `/status` — статус ядра
- `/proactive on|off`

### Голосовые сообщения

- Telegram sends OGG/Opus
- Bot: ffmpeg → WAV 16kHz → Aura ASR (JSON-RPC `voice.command`)
- Response: TTS → OGG → sendVoice

### Безопасность

- **Pairing:** QR или 6-значный код в CLI
- **JWT:** Bot ↔ Core через mTLS
- **Whitelist:** только свой Telegram ID (ADMIN_IDS env)
- **Rate limit:** 10 команд/мин на user
- **НЕ хранит** историю (Telegram и так хранит, но у нас — только session)

### Деплой

- Local: `systemd --user aura-bot.service`
- VPS: Docker (для удалённого доступа)
- **Но:** ADR-031 — не облако. Только self-hosted.

### Что НЕ делаем

- SaaS-бот для всех (privacy)
- Публичный бот (только для своего ядра)
- Inline-режим (YAGNI)

## Последствия

**Плюсы:** первый мобильный UX за 3-5 дней, не нужен Android SDK
**Минусы:** Telegram = внешний сервис (privacy trade-off, документируем)

## Связанные
- ADR-029 (Multi-client)
- ADR-032 (JSON-RPC)
