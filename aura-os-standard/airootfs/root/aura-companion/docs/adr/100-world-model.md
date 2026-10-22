# ADR-100: World Model

**Дата:** 2026-10-02
**Статус:** Принято (MVP)

## Контекст
Aura не знает состояние системы: что открыто, какие файлы, что запущено.
Без World Model → нет Capability Graph → нет Cognitive.

## Решение
`aura/core/world_model.py`:
- scan_windows() — wmctrl -l
- scan_processes() — ps top CPU
- scan_recent_files() — find -mmin
- WorldModel.refresh() — обновить
- WorldModel.summary() — текст для голоса

Агент `world_state` — «что в системе?».

## YAGNI
- Не пишем свой ps/top — используем системные
- Не сканируем весь диск — только home, maxdepth 3

## Ссылки
ADR-099 (BT Integration), ADR-101 (Capability Graph)
