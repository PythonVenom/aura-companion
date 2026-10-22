# ADR-025: Aura Lite (без LLM)

**Дата:** 2026-09-28
**Статус:** Принято

## Контекст

qwen2.5:7b требует 8 ГБ RAM + GPU. На Celeron, Pi Zero,
старых ноутбуках и Android — не запустится. Нужен режим без LLM.

## Решение

**Aura Lite** — флаг `--no-llm`:
- Brain отключён
- ~40 rule-based агентов работают
- LLM-запросы → «Не могу ответить в Lite-режиме»

### Работает без LLM

- Время, погода, будильник, таймер
- Музыка, громкость, ducking
- Вкладки, приложения, окна
- Чек-лист, журнал, напоминания
- Макс/TG/VK
- Proactive триггеры
- HealthAgent, TimeAgent

### НЕ работает

- «Расскажи про космос»
- «Что такое X»
- Свободный диалог

### Требования

- RAM: 512 МБ
- CPU: 1 ядро x86_64 / ARMv7
- Диск: 200 МБ

### Запуск

    aura_main --no-llm

Или: `aura settings set brain_enabled false`

## Связанные

- ADR-014 (Proactive)
- ADR-022 (cross-platform)
- ADR-024 (Android)
