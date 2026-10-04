# ADR-022: Cross-platform strategy

**Дата:** 2026-09-28
**Статус:** Принято

## Контекст

Аура выходит за пределы Arch. Нужна стратегия портов без дублирования кода.

## Решение

### Принцип: один код — разные backend'ы

Весь платформо-зависимый код в `aura/platform/` (ADR-017). Агенты не знают про ОС.

### Порядок портов

1. **Arch Linux** — 100% сначала (текущая)
2. **Ubuntu/Debian** — Q1 2027
3. **Windows** — Q2 2027
4. **Android** — Q3 2027 (Termux)
5. **macOS** — Q4 2027

### Что НЕ делаем

- Нативные приложения (это web-версии)
- Свой системный трей (используем ОС)
- Свой синтез речи (Piper везде)

### Ограничения

- **Android** — нет Ollama
- **Windows/macOS** — нет MPRIS
- **macOS** — нотаризация $99/год

## Компоненты

- `aura/platform/{linux,ubuntu,windows,macos}.py`
- `install_{ubuntu,windows,macos,android}.sh/ps1`
- CI matrix: ubuntu + windows + macos
- `docs/cross-platform.md`

## Последствия

Плюсы: один код — все ОС, прозрачные ограничения, быстрое добавление новых.
Минусы: первые 2 недели рефакторинг без новой функциональности.

## Связанные

- ADR-017: Platform Abstraction Layer
- ADR-019: Installation Experience
