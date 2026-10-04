# Checkpoint — 2026-10-04 — Elder care MVP 5/5

## Итог дня

- **15 коммитов** за сессию
- **MLP бати 5/5**: SOS, Лекарства, Звонок, Погода, Музыка ✅
- **CI зелёный** (последние 3 runs success)
- **Задач: 12/81** (14%)

## Закрыто в v7.2 (12 задач)

- T001 reboot-recovery
- T002 backup БД + systemd timer
- T003 friendly log
- T004 LLM fallback (7b → 3b → 270m → template)
- T005 CI Ubuntu fix (setuptools<81 + python-multipart)
- T006 README 10 осей
- T007 whitelist активации (фразы без "аура")
- T008 music Bug60
- T071 PyPI (build готов, upload отложен)
- T072 AUR (PKGBUILD готов)
- T074 AppImage (build.sh готов)
- T075 Docker (Dockerfile + compose)

## Закрыто в v7.3 (4 задачи)

- T011 SOS голосовой
- T012 детектор падения
- T014 экстренный контакт
- T018 паническая кнопка в трее
- T043 call agent (4 режима)

## Закрыто в v7.4 (1 задача)

- T022 medication reminder (SQLite + scheduler)

## Изменения инфраструктуры

- `aura/bootstrap.py` — 5 новых агентов (sos, meds, fall, call, + 2)
- `tests/test_bootstrap.py` — AURA_TEST_ROBUST_V1 (не ломается при добавлении агентов)
- `aura/agents/brain.py` — LLM fallback chain
- `aura/core/tray.py` — SOS кнопка
- `packaging/` — AppImage, AUR, Docker

## Что дальше

**v7.3 (осталось 4/8):**
- T013 BT-кнопка SOS (железо)
- T015-T017 детекторы газа/дыма/воды

**v7.4 (9/10):**
- T021 мед БД расширить (аллергии, диагнозы)
- T023 тонометр BT
- T024 визиты к врачу
- T025 взаимодействие лекарств
- T026-T030 FinElder (ЖКХ, ЦБ, антискам, пенсия)

**v7.5-v7.8:**
- ТВ CEC, Matter, HomeAssistant
- WhatsApp, VK, email
- Companion mode
- uk, kk, de, fr

## Дата

2026-10-04 22:37
