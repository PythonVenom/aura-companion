# ADR-162: Radiation-tolerant storage (P3 #158)

**Дата:** 2026-10-14  
**Статус:** Accepted  
**Контекст:** P3, космические задачи. Вдохновлено memory scrubbing на RAD750, JWST.

## Проблема

Критичные данные AURA (stress.db, meds.db, recall.db) на диске уязвимы к:
1. **Bit-flip** — случайное изменение бита (космическая радиация, сбой ОЗУ/ФС).
2. **Silent corruption** — порча без ошибки чтения.
3. **Сбои ФС** — потеря сектора без уведомления.

Для elder-care потеря записи о лекарстве = критический инцидент.

## Решение

Модуль `aura/core/rad_storage.py`:

- **`crc32(data)`** — контрольная сумма для верификации.
- **`Block`** — данные + CRC32.
- **`RadiationTolerantStore`** — triple-copy + CRC + scrub.

Формат на диске:
