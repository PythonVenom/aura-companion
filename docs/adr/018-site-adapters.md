# ADR-018: Site Adapters

**Дата:** 2026-09-28
**Статус:** Принято
**Связано:** ADR-016, ADR-013, ADR-017

## Контекст

Firefox Bridge для Макса работает. Нужно расширить на другие сайты:
- Telegram Web K
- VK
- YouTube (низкий приоритет)

## Решение

**SiteAdapter pattern.** Один content script на сайт, единый native
host, разные Python-агенты.

### Структура

    firefox_extension/
    ├── background.js          (общий роутинг по URL)
    ├── content_max.js         ✅
    ├── content_telegram.js    ✅
    ├── content_vk.js          ✅
    └── content_youtube.js     🟢 потом

    aura/agents/
    ├── messenger.py           ✅ Макс
    ├── telegram.py            ✅
    └── vk_web.py              ✅

### Общий контракт

Каждый content script отвечает на одинаковые actions:
- list_chats → [{name, preview, index}]
- find_chat → {found, name}
- send_message → {typed, text}
- finalize_send → {sent}
- clear_input → {ok}

Каждый агент:
- can_handle(request) — по ключевым словам
- handle(request) — через send_command({"action": ...})

### Приоритет

1. Telegram Web K — общение. 4-6 ч.
2. VK — большая РФ-аудитория. 2-3 ч.
3. YouTube — редкий сценарий. 2 ч.

## Что НЕ делаем

- Нативные приложения (разные SDK)
- API-интеграции (ключи, лимиты)
- MV3 (пока MV2 стабильнее)

## Связанные

- ADR-016: SiteAdapter 5 уровней
- ADR-017: Platform Abstraction Layer
