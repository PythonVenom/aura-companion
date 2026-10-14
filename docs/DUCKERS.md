# Duckers — две системы приглушения звука

## Зачем две?

Aura имеет два архитектурных слоя:
- **Companion** (`aura/`) — main, активно развивается
- **Kernel** (`aura/kernel/`) — legacy (ADR-004), поддерживается

Каждый слой имеет свой ducker.

## Сравнение

| Свойство | `AgentMusicDucker` | `AudioDuckerAgent` |
|----------|-------------------|---------------------|
| Путь | `aura/agents/music_ducker.py` | `aura/kernel/agents/audio_ducker.py` |
| Слой | Companion | Kernel |
| Стиль | Sync | Async |
| API | `duck()` / `un_duck()` | Подписка на события |
| События | — | `voice.wake`, `speaker.started`, `speaker.spoken` |
| Кто вызывает | `speaker.py:40` (Bug 32) | `kernel/bootstrap.py:72` |
| Строк | 122 | 179 |

## Когда какой использовать

**Companion (main):** `AgentMusicDucker`
- Простой API: `duck()` перед речью → `un_duck()` после
- Используется в `speaker.py` для Bug 32 (ducking при речи)

**Kernel (legacy):** `AudioDuckerAgent`
- Реактивный: подписан на события шины
- Работает в kernel-контексте

## Не объединять!

Попытка объединить сломает:
- Sync vs async контракт
- Разные шины событий (companion bus vs kernel bus)
- Разные bootstrap-цепочки

Наука: Fowler 2009 (Refactoring) — не сливать разные ответственности.
