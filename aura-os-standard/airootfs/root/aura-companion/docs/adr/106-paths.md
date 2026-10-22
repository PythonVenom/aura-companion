# ADR-106: Paths Module

**Дата:** 2026-10-02
**Статус:** Принято

## Контекст
Хардкод `~/aura_project/` в 10+ агентах. Aura нельзя установить в /opt.
Блокер для дистрибутивов.

## Решение
`aura/paths.py`:
- PROJECT_DIR — резолвится от __file__
- CACHE_DIR — ~/.cache/aura (env AURA_CACHE_DIR)
- CONFIG_DIR — ~/.config/aura (env AURA_CONFIG_DIR)
- MODELS_DIR — внутри проекта

Все агенты импортируют через `__import__("aura.paths", ...)`.

## Ссылки
ADR-017 (PAL), ADR-100 (World Model)
