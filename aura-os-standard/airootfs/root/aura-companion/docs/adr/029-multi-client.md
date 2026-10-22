# ADR-029: Multi-client architecture

**Дата:** 2026-09-28
**Статус:** Принято

## Контекст

Аура — не один клиент. Пользователи разные:
- Разработчик — CLI + KDE widget
- Бабушка — flash-install + голос
- Доктор — Android-клиент
- Молодёжь — Telegram бот

## Решение

Ядро + клиенты. Ядро одно, клиенты разные.

### Ядро

    Aura Core (Python, MIT)
    ├── 31 агент
    ├── LLM/ASR/TTS локально
    └── JSON-RPC через HTTPS + WebSocket

### Клиенты (отдельные репо)

| Клиент | Стек | Репо | Лицензия |
|---|---|---|---|
| CLI | Python | aura-companion | MIT |
| KDE tray | QML | aura-companion/contrib | MIT |
| Web UI | htmx | aura-web | MIT |
| Android | Kotlin | aura-client-android | MIT |
| Telegram bot | Python | aura-bot | MIT |
| iOS | Swift | aura-client-ios | MIT |
| Box firmware | Shell | aura-box | MIT |

### Протокол

- **Discovery:** mDNS (`aura.local`) в LAN
- **Удалённо:** WireGuard VPN
- **Auth:** mTLS + JWT (TTL 15 мин)
- **API:** JSON-RPC 2.0
- **Push:** WebSocket (real-time)

### Безопасность

- Клиент ↔ ядро: WireGuard + mTLS
- Ключ шифрования только у пользователя
- Zero-knowledge для медицинских данных

## Что НЕ делаем

- Монолит один клиент под всё
- Облачный сервер (только локально)
- OAuth через внешних провайдеров

## Связанные

- ADR-022 (cross-platform)
- ADR-024 (Android)
- ADR-026 (Medical)
