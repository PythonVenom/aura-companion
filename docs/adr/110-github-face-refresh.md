# ADR-110: GitHub Face Refresh

**Статус:** Accepted
**Дата:** 2026-10-02

## Контекст

GitHub-репо — публичное лицо Aura. После каждого релиза витрина
должна отражать реальность. И быть мультиязычной.

## Решение

- `README.md` (en default) + `README.ru.md`, `README.zh.md`, `README.es.md`
- Бейджи: tests, ADR, handlers, PRR-carma
- Раздел "What's new" автоген из git log
- ROADMAP — только в `docs/internal/`, не на витрине
- `scripts/prr/face_check.py` — битые ссылки
