# ADR-004: Ревизия мёртвого кода в монолите

## Дата
2026-09-20

## Статус
Принято

## Контекст

После закрытия Фазы 1 (ADR-003, migration-roadmap.md) мы начали
Фазу 2 — миграцию `upgrader`. При чтении `agents/upgrader.py`
обнаружилось: агент создаётся, но **никогда не вызывается**.
Флаг `waiting_for_confirmation` всегда `False`, блок в главном цикле
не выполняется.

Это поставило вопрос: сколько ещё таких агентов в монолите?

## Метод ревизии

Разобрали `aura_core.py` через **Python AST** (не `grep` — он не видит
многострочных вызовов).

Критерий «мёртвый агент»:
- Агент создаётся в `AuraCore.__init__` (`self.agents = {...}`).
- **Не упоминается** ни в `self.agents['X']` (прямое обращение),
- ни в лямбдах `tool_router.register(...)` (косвенное обращение).

## Результат

| Метрика | Значение |
|---|---|
| Создаётся агентов | 80 |
| Прямо используется | 21 |
| Мёртвых | 59 |

**74% кода монолита — мёртвый код.**

### Живые (21)

`app_launcher`, `audio_pult`, `audio_router`, `brain`, `browser_tabs`,
`functions`, `internet`, `journal`, `listener`, `media_search`, `power`,
`rag_memory`, `registry`, `screen_reader`, `speaker`, `time`,
`tool_router`, `updates`, `upgrader`, `vk_music`, `window_control`.

Замечание: `upgrader` — **особый случай**. Создаётся, флаг проверяется,
но флаг никогда не ставится в `True`. То есть **почти мёртвый** —
считаем мёртвым для целей миграции.

### Мёртвые (59)

`app_controller`, `auto_reboot`, `auto_task`, `barge_in`,
`browser_controller`, `code_autopilot`, `code_helper`, `conscious`,
`context`, `context_memory`, `cosmic`, `digital_twin`, `dream`,
`emotion`, `energy`, `exoskeleton`, `focus_switch`, `future_ui`,
`ghost`, `global`, `grid`, `harmonizer`, `health`, `hybrid_core`,
`infinite`, `interrupt`, `journal_browser`, `keeper`, `life`,
`master_key`, `media`, `media_pult`, `mirror`, `mouse`, `music_ducker`,
`offline_first`, `parallel_universe`, `planet`, `post_apocalypse`,
`prime`, `quantum`, `reality`, `router`, `security`, `self_update`,
`smart_browser`, `smart_home`, `survivor`, `system`, `task_executor`,
`task_manager`, `text_editor`, `time_loop`, `update_watcher`, `vault`,
`vision`, `vortex`, `weather`, `window_manager`.

## Категории мёртвых

### Категория 1 — философско-декоративные (13)

`quantum`, `master_key`, `harmonizer`, `dream`, `emotion`, `energy`,
`vortex`, `reality`, `cosmic`, `keeper`, `infinite`, `future_ui`,
`global`, `prime`, `conscious`.

**Суть:** 25–40 строк, `execute()` возвращает строку-заглушку.
Реальной логики нет. Эксперименты-эскизы.

**Решение:** не мигрировать в модуль. Идеи сохранить в `docs/ideas.md`
(если там есть что сохранять — у большинства только поэтическая метафора).

### Категория 2 — заделы на будущее (5)

`life_simulator`, `time_loop`, `digital_twin`, `mirror_world`,
`exoskeleton`.

**Суть:** есть **структура** (данные, команды), нет **связи с внешним
миром**. Идеи рабочие, реализации — нет.

**Решение:** не мигрировать сейчас. Идеи сохранить в `docs/ideas.md`
с описанием, **что нужно** для реализации (когда понадобится).

### Категория 3 — рабочие, но не подключены (1)

`parallel_universe`.

**Суть:** **работает** — фоновый поток, анализ вкладок браузера через
`wmctrl`. Просто не зарегистрирован в `tool_router`.

**Решение:** **мигрировать** в модуль и подключить к `tool_router`.

### Категория 4 — опасные (1)

`ghost`.

**Суть:** создаёт анонимные комнаты (Tor + VPN, honeypots).
**Работает** технически, но требует решения по безопасности.

**Решение:** **не мигрировать** сейчас. Отдельное решение — нужно ли
это вообще, и если да — с какими ограничениями.

### Категория 5 — дубли и неиспользуемые (39)

Всё остальное. Дубли (`update_checker`, `update_notifier`,
`update_watcher`, `auto_task`, `auto_reboot` — все про обновления)
или реальные функции без подключения (`smart_home`, `task_manager`,
`media_center`, `code_helper`, `vault`, `security`, `vision`, `weather`,
`mouse`, `focus_switch`, `music_ducker`, `system`, `text_editor`,
`router`, `interrupt`, `barge_in`, `offline_first`, `survivor`, `grid`,
`post_apocalypse`, `hybrid_core`, `health`, `media_pult`, `window_manager`,
`context`, `context_memory`, `code_autopilot`, `smart_browser`,
`browser_controller`, `journal_browser`, `app_controller`).

**Решение:** **не мигрировать все разом**. Решить судьбу **по группам**:
- Дубли (обновления): оставить **один**, остальные — в `docs/ideas.md`.
- Реальные функции: решить, **какие нужны** для альфы (подключить),
  какие — **отложить** (в `docs/ideas.md`).

## Решение

1. **Фаза 2 (migration-roadmap.md) закрывается без миграции.**
   `upgrader` — мёртв, мигрировать нечего.
2. **Фаза 4 переформулирована:**
   - Мигрировать **8 живых** агентов (из 21 — 13 уже в модуле).
   - Мёртвые **не мигрировать** — решать судьбу **в модуле**, не таща
     балласт из монолита.
3. **Список мёртвых — в `docs/dead-code.txt`** (для истории).
4. **Идеи из мёртвых — в `docs/ideas.md`** (для будущего).
5. **Монолит не трогаем.** Мёртвые агенты уйдут вместе с ним на Фазе 5.

## Последствия

**Положительные:**
- Точная карта: 21 живой, 59 мёртвых.
- Фаза 4 сокращена с ~57 до ~8 агентов.
- Идеи сохранены, не потеряны.
- Балласт не тащим.

**Отрицательные:**
- 59 файлов в `agents/` — мёртвый груз до Фазы 5.
- Категоризация некоторых (особенно категории 5) — предварительная.
  Финальное решение — по мере развития модуля.

**Риски:**
- Если **ошиблись** с категорией и выкинули нужное — вернёмся к эскизам
  в `docs/ideas.md`, восстановим.
- Если **ошиблись** с «мёртвый» (агент используется косвенно, AST не
  поймал) — при миграции обнаружитcя, разберёмся.

## Ссылки
- ADR-001 — модульная архитектура
- ADR-002 — интеграция Orchestrator
- ADR-003 — паритет `aura_main.py`
- `docs/migration-roadmap.md` — план вывода монолита
- Fowler, «Refactoring» 2nd ed. — «Preserve knowledge, delete code»
- YAGNI (Ron Jeffries, XP)
