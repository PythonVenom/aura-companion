# ADR-023: Voice Customization

**Дата:** 2026-09-28
**Статус:** Принято

## Контекст

Пользователь должен мочь изменить:
- имя ассистента (wake-word)
- голос TTS
- скорость речи

Это критично для accessibility: бабушка хочет назвать ассистента
«Катя», незрячий — «Маруся», ребёнок — «Света».

## Решение

### Настройки в JSON

    ~/.config/aura/settings.json

**Параметры:**
- wake_word — основное слово
- wake_word_aliases — варианты
- tts_voice — модель Piper
- tts_speed — 0.5..2.0
- volume — 0..100

### CLI

    aura settings show
    aura settings get wake_word
    aura settings set wake_word катя

### Автоподхват

При старте `aura_main` читает settings, применяет:
- `fsm._is_activated` использует `wake_word + aliases`
- `speaker.say` использует `tts_voice`, `tts_speed`, `volume`

### Что НЕ делаем (YAGNI)

- GUI для настроек (CLI + JSON достаточно)
- Свои TTS-модели (только Piper)
- Смена языка (пока ru/en)

## Последствия

**Плюсы:**
- Accessibility (имя пользователя)
- Персонализация (голос, скорость)
- Один JSON — легко бэкапить

**Минусы:**
- Нужно перезапустить сервис после смены
- Нет горячего reload (в планах)

## Связанные

- ADR-012 Dialog FSM (активация)
- ADR-017 Platform Abstraction Layer
