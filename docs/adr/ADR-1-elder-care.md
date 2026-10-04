# ADR-XXX: Профиль Elder Care

Статус: Accepted
Дата: 2026-10-04

## Контекст

Aura нужна бате (Pentium 6405U, 8GB). Требования elder care
отличаются от обычного пользователя:

- Длинные паузы в речи → стандартный endpointing 700 мс режет фразы
- Требуется подтверждение действий
- Нельзя перебивать (BargeIn off)
- Явные состояния (не оставлять в тишине)
- Устойчивость к формулировкам («чё на улице» = «погода»)

Наука: Portet 2013, Ryan 1995, Fisk 2009, Czaja 2018.

## Решение

1. Отдельный профиль `config/profiles/elder.json`.
2. Роутинг через env `AURA_PROFILE=elder`.
3. Параметры профиля переопределяют listener/speaker/orchestrator:
   - MIN_TURN_SILENCE 0.8 → 1.8
   - tts_speed 1.0 → 0.9
   - barge_in on → off
   - confirm_actions on
4. Guard: не отдавать в LLM фактические вопросы без агента.
5. Capability Matrix — скрипт аудита ячеек.

## Backlog (v7.2+)

- SOS emergency с реальным звонком
- Соцсети VK/OK/RuTube/WhatsApp
- Браузерный bridge (Edge/Yandex)
- Companion mode
- Песочница плагинов
- Режимы tool/companion/care

## Последствия

- Одна кодовая база, разные профили
- Elder care поддержан без ломки основного UX
- Default профиль (pythonvenom) не затронут

## Альтернативы

- Отдельная fork для elder — отвергнуто (дублирование)
- Runtime-morph ты/вы — отвергнуто (морфология)
- Хардкод параметров — отвергнуто (негибко)
