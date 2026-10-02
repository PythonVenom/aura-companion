# ADR-098: Resolution Cascade

**Дата:** 2026-10-02
**Статус:** Принято (MVP)

## Контекст
«Аура, открой DeepSeek» — не работало. Нет механизма поиска цели
с fallback: приложение → окно → вкладка → web.

## Решение
ResolutionCascade — 4 ступени:
1. **App** — установленное приложение (which, desktop)
2. **Window** — открытое окно (wmctrl, xdotool)
3. **Browser** — открытая вкладка (Firefox bridge)
4. **Web** — новая вкладка + поиск

Первая с результатом побеждает. Логирование в Logbook.

## Ссылки
ADR-094 (Behavior Tree), ADR-093 (Copilot)
