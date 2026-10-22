# Настройки Aura

Все настройки в одном JSON: `~/.config/aura/settings.json`.

## Параметры

### wake_word (string)
Основное слово активации. По умолчанию: `аура`.

    aura settings set wake_word катя

### wake_word_aliases (list)
Альтернативные варианты (для устойчивости ASR). По умолчанию:
`ара`, `ура`, `алло`, `аула`.

### tts_voice (string)
Голос Piper. По умолчанию: `ru_RU-irina-medium`.
Сменить: положить другую модель в `voices/`.

### tts_speed (float)
Скорость речи: 0.5 (медленно) — 2.0 (быстро). По умолчанию: 1.0.

### volume (int)
Громкость TTS: 0–100. По умолчанию: 100.

### notifications (bool)
Показывать системные уведомления. По умолчанию: true.

### proactive_enabled (bool)
Proactive-режим (Аура говорит первой). По умолчанию: true.

### language (string)
Язык: `ru` или `en`. По умолчанию: `ru`.

## CLI

Показать все:

    aura settings show

Получить значение:

    aura settings get wake_word

Установить:

    aura settings set volume 80

Файл:

    cat ~/.config/aura/settings.json
