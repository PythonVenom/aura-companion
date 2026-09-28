# ADR-032: JSON-RPC Protocol

**Дата:** 2026-09-28
**Статус:** Проект
**Связано:** ADR-029 (Multi-client)

## Контекст

ADR-029: ядро + клиенты через JSON-RPC. Нужна детализация:
форматы, auth, версии, ошибки.

## Решение

### Транспорт

- **LAN:** WebSocket `ws://aura.local:8765/rpc` (mDNS discovery)
- **WAN:** WireGuard + WebSocket `wss://<box>:8765/rpc`
- **Auth:** mTLS (клиентский серт) + JWT (TTL 15 мин)

### Формат запроса

    {
      "jsonrpc": "2.0",
      "id": "uuid-v4",
      "method": "voice.command",
      "params": {"text": "какие таймеры"},
      "meta": {"client": "android-1.0", "locale": "ru"}
    }

### Формат ответа

    {
      "jsonrpc": "2.0",
      "id": "uuid-v4",
      "result": {"text": "⏱ Активных нет", "audio_url": null},
      "error": null
    }

### Методы (v1)

| Method | Направление | Описание |
|---|---|---|
| `voice.command` | client→core | Голос/текстовая команда |
| `voice.stream` | core→client | SSE поток TTS-аудио |
| `agent.list` | client→core | Список агентов |
| `agent.call` | client→core | Прямой вызов агента |
| `state.subscribe` | client→core | Подписка на state (WebSocket) |
| `proactive.notify` | core→client | Push проактивного сообщения |
| `settings.get` / `settings.set` | client→core | Настройки |

### Версионирование

- `/rpc` — текущая (v1, стабильная)
- `/rpc/v2` — когда breaking changes
- В meta: `client` содержит версию → graceful degradation

### Ошибки (стандарт JSON-RPC 2.0)

| Код | Значение |
|---|---|
| -32700 | Parse error |
| -32600 | Invalid Request |
| -32601 | Method not found |
| -32602 | Invalid params |
| -32603 | Internal error |
| -32000 | Aura: agent not found |
| -32001 | Aura: ASR failed |
| -32002 | Aura: LLM unavailable |
| -32003 | Aura: auth required |
| -32004 | Aura: rate limited |

### Безопасность

- mTLS: клиентский серт выдаёт ядро при pairing (QR-код)
- JWT: подписан HS256, секрет в `/etc/aura/jwt.key`
- Rate limit: 60 req/min на клиента
- Audit log: все `agent.call` с danger=true → в журнал

### Что НЕ в v1

- GraphQL (overkill для 7 методов)
- gRPC (нужен protoc, тяжело для клиентов)
- REST (WebSocket лучше для push)
- OAuth (только mTLS+JWT)

## Последствия

**Плюсы:**
- 7 методов покрывают все сценарии клиентов
- JSON-RPC 2.0 — стандарт, все языки имеют библиотеки
- WebSocket — real-time push

**Минусы:**
- Нужен TLS-менеджмент (cert rotation)
- WireGuard setup для удалёнки (документация)

## Связанные

- ADR-029 (Multi-client)
- ADR-022 (cross-platform)
