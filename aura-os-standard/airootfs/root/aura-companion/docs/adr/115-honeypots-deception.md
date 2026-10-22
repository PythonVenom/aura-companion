# ADR-115: Honeypots & Deception

**Статус:** Accepted
**Дата:** 2026-10-02

## Контекст

Aura имеет физический доступ к дому. Defense in depth требует deception.

## Решение

3 слоя:
1. **Canary tokens** — файлы-приманки, при касании → alert + panic
2. **Tarpit endpoints** — фейк-action'ы (`admin.shell`, `auth.bypass`)
3. **Rat-trap handlers** — зеркала, имитирующие уязвимость

Реализация — v4.0 код.
