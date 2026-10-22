# ADR-085: Care Coordinator + Briefing

**Дата:** 2026-10-02
**Статус:** Принято (MVP)

## Контекст
Пользователь забывает есть/пить/таблетки/сон. Aura = опора (ADR-057).

## Решение
Care Coordinator на базе Logbook.
- Утренний брифинг (8:00)
- Вечерний брифинг (22:00)
- Hydration reminder (каждые 2 часа)
- Medication reminder (по расписанию)
- Sleep reminder (23:00)

## Компоненты
- aura/agents/care.py (CareAgent)
- aura/agents/briefing.py (BriefingAgent)
- Triggery: время, события, паттерны

## Связь с Logbook
Briefing читает logbook: "вчера закрыл Bug 72, начал installer".
Care пишет logbook: "напомнил поесть в 14:30".

## YAGNI
- Не пишем свой календарь (берём из logbook)
- Не пишем свой sleep tracker (позже)
- Не автоматизируем (только напоминаем)

## Ссылки
ADR-057 (accessibility-first), ADR-084 (Logbook)
