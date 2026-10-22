# ADR-008: Вывод монолита из эксплуатации

## Дата
2026-09-22

## Статус
Принято

## Контекст

С момента ADR-002 (интеграция Orchestrator в systemd, 2026-09-20)
монолит `aura_core.py` оставался fallback через `AURA_USE_ORCHESTRATOR=0`.

К 2026-09-22 все 4 критерия вывода (roadmap) выполнены:

1. **Все агенты мигрированы или выброшены.**
   AST-проверка: 80 агентов в монолите, 21 живой, 20 мигрированы,
   59 мёртвых (ADR-004), `upgrader` — дубль `updates`.

2. **AuraCore.process() воспроизведён в модуле.**
   Три уровня роутинга (ADR-005): registry → tool_router → brain.
   Главный цикл aura_main.py = AuraCore.run() (ADR-003).

3. **Главный цикл = по поведению** (переформулирован).
   Монолит нестабилен — зависает, падает (проверено дважды).
   Модуль реализует все функции монолита (тесты + живые прогоны).

4. **Fallback не нужен** (переформулирован).
   `journalctl --since "7 days ago"`: 1 запуск fallback — до ADR-002.
   С момента ADR-002: 0 запусков fallback.

Дополнительно: Фаза 6 завершена — 12 заготовок портированы
(vault, security, task_manager, music_ducker, focus_switch,
parallel_universe, window_manager, context_memory, media_pult,
text_editor, vision, mouse).

Проверка зависимостей модуля:
- `grep "from agents." aura/ aura_main.py` — пусто
- `grep "import aura_core" aura/ aura_main.py` — пусто
- `aura_main.py` импортирует только из `aura.*`

## Решение

**Перенести монолит в `attic/`** (не удалять).

Порядок:
1. `git tag legacy-monolith-final` — бэкап-точка.
2. `mkdir -p attic`.
3. `git mv aura_core.py attic/`.
4. `git mv agents/ attic/`.
5. `git mv run_aura.sh.bak_core attic/` (если есть).
6. Убрать ветку `else` из `run_aura.sh` (только aura_main.py).
7. Убрать `Environment="AURA_USE_ORCHESTRATOR=1"` из systemd-юнита.
8. `daemon-reload`, `restart`, проверка.
9. Коммит.

**Через 7 дней:** `git rm -r attic/` — окончательное удаление.

**Почему attic, а не rm сразу:**
Strangler Fig (Fowler, 2004): не убиваем дерево мгновенно.
Переносим в архив, наблюдаем. Если не понадобится — удаляем.
Обратимо → необратимо. Bezos: тип 2 → тип 1.

## Последствия

**Положительные:**
- Модуль — единственная работающая система Ауры.
- Нет двойной поддержки (монолит + модуль).
- Нет дрейфа поведения между системами.
- Убрана путаница «какой режим запущен».

**Отрицательные:**
- Fallback недоступен (но не использовался 2 дня).
- attic/ занимает место в репо (7 дней).

**Риски:**
- Если модуль сломается критично — нет быстрого отката
  через флаг. Митигация: `git tag legacy-monolith-final` — можно
  восстановить из тега. Через 7 дней — из истории git.
- systemd перезапустит модуль при падении (Restart=on-failure).

## Проверка

1. `git tag -l legacy-monolith-final` → тег есть.
2. `ls attic/` → aura_core.py, agents/.
3. `ls` (корень) → нет aura_core.py, нет agents/.
4. `run_aura.sh` → только aura_main.py.
5. `systemctl --user status aura.service` → active (running).
6. Ручной прогон: «Аура, который час» → работает.

## Ссылки
- ADR-001 — модульная архитектура
- ADR-002 — интеграция Orchestrator в systemd
- ADR-003 — паритет aura_main.py с AuraCore.run()
- ADR-004 — ревизия мёртвого кода
- ADR-005 — LLM-роутинг
- ADR-006 — barge-in архитектура
- ADR-007 — AEC через PipeWire echo-cancel
- docs/migration-roadmap.md
- Fowler, «StranglerFigApplication», 2004
