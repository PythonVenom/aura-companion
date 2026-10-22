# ADR-032: JSON-RPC Protocol

**Дата:** 2026-09-28
**Статус:** Проект
**Связано:** ADR-029

## Контекст

ADR-029: ядро + клиенты. Нужны форматы, auth, версии, ошибки.

## Решение

### Транспорт
- **LAN:** WebSocket `ws://aura.local:8765/rpc` (mDNS)
- **WAN:** WireGuard + `wss://<box>:8765/rpc`
- **Auth:** mTLS + JWT (TTL 15 мин)

### Формат

Запрос:

    {
      "jsonrpc": "2.0",
      "id": "uuid-v4",
      "method": "voice.command",
      "params": {"text": "какие таймеры"},
      "meta": {"client": "android-1.0", "locale": "ru"}
    }

Ответ:

    {
      "jsonrpc": "2.0",
      "id": "uuid-v4",
      "result": {"text": "⏱ Активных нет"}
    }

### Методы (v1)

| Method | Направление | Описание |
|---|---|---|
| `voice.command` | client→core | Команда |
| `voice.stream` | core→client | SSE TTS-аудио |
| `agent.list` | client→core | Список агентов |
| `agent.call` | client→core | Прямой вызов |
| `state.subscribe` | client→core | Подписка |
| `proactive.notify` | core→client | Push |
| `settings.get`/`set` | client→core | Настройки |

### Ошибки (JSON-RPC 2.0)

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
- mTLS: серт при pairing (QR)
- JWT: HS256, секрет в `/etc/aura/jwt.key`
- Rate limit: 60 req/min
- Audit log: danger=true → журнал

### НЕ в v1
- GraphQL (overkill)
- gRPC (protoc тяжело)
- REST (WebSocket лучше)
- OAuth

## Связанные
- ADR-029 (Multi-client)
- ADR-022 (cross-platform)
