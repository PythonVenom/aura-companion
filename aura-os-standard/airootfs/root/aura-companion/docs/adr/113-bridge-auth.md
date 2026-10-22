# ADR-113: Bridge Auth

**Статус:** Accepted
**Дата:** 2026-10-02

## Контекст

Bridge socket `/tmp/aura_firefox.sock` — world-writable поверхность.
Любой процесс может послать `power.off` или `vk.send_message`.

## Решение

1. Токен в `~/.config/aura/bridge_token` (chmod 600, 32 hex).
2. При старте расширения — token передаётся в native messaging host (env).
3. `aura/core/bridge.send_command` добавляет `_token` в payload.
4. Расширение (background.js) отклоняет без валидного `_token`.
5. Perms на socket: 600 (только user).

## Миграция

- v4.0-alpha: токен генерируется, но валидация **мягкая** (warning).
- v4.0-beta: валидация строгая.
- v5: TLS + per-extension tokens.

## Последствия

- (+) защита от спуфинга (STRIDE-S в ADR-111)
- (+) обратно совместимо (мягкий режим)
- (−) токен надо распространять между Aura ↔ расширением
