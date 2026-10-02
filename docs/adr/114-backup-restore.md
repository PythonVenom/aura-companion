# ADR-114: Backup / Restore / Migration

**Статус:** Accepted
**Дата:** 2026-10-02

## Контекст

Journal, care, logbook, chat — всё в `~/.cache/aura/` и `~/.config/aura/`.
Потери = потеря памяти Aura. Нужен бэкап + восстановление.

## Решение

- `scripts/backup.sh` → `~/aura_backups/aura-YYYYMMDD-HHMMSS.tar.gz`
- `scripts/restore.sh <archive>` — с подтверждением
- Исключаем сокеты и логи
- Ротация (хранить 7 последних) — v5
- Автобэкап раз в день (systemd timer) — v5

## Последствия

- (+) простая защита от потери памяти
- (+) миграция между машинами
- (−) ручной запуск пока
