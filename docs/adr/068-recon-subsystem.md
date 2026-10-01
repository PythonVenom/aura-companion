# ADR-068: Recon Subsystem

## Статус
Принято

## Дата
2026-10-01

## Контекст

Диагностика проекта требует ручного копипаста команд из чата в терминал.
zsh обрывает paste >1024 символов. Это создаёт трение в цикле
«ассистент → терминал → ассистент» и ограничивает темп X10.

Проблема не в командах, а в формате обмена. Нужен структурированный
протокол «задача → команды → вывод».

## Решение

Подсистема `aura_recon`:
- Задачи описаны в файлах `scripts/recon_tasks/<tag>.tasks`
- Runner прогоняет команды, собирает вывод
- Formatter пишет markdown-отчёт
- Отчёт копируется в clipboard (`wl-copy`)

### Формат .tasks

    # tag: base
    # description: базовое состояние проекта

    ## id=01 name=git-state
    cmd: git status --short
    cmd: git log --oneline -5

    ## id=02 name=unit-file
    file: ~/.config/systemd/user/aura.service

    ## id=03 name=python-block
    heredoc:
    from aura.agents.listener import AgentListener
    print(AgentListener)

### Три типа записей
- `cmd:` — shell-команда (2–3 на задачу, по правилу zsh)
- `file:` — дамп файла
- `heredoc:` — Python/Shell с одинарными кавычками

### CLI

    aura_recon <tag> [--out DIR] [--clip] [--quiet]
    tag ∈ {base, bugs, widget, dbus, service, all}

Выход: `~/aura_private/recon/<TS>_<tag>.md`

### Graceful degradation
- Упавшая команда → `[exit=N]`, runner едет дальше
- Файл не найден → `[missing]`
- Таймаут 5 сек → `[timeout]`
- `set -u` без `set -e`
- Атомарная запись (tempfile → rename)
- Никогда не пишет в `~/.config`, `/etc`

### Защита
- Whitelist команд? Нет. Recon = диагностика, не sandbox.
- Но: `aura_recon` не запускает `systemctl start/stop` — только read-only
- Write-операции (restart, kill) — через ControlService, не Recon

## Последствия

- Скорость цикла «ассистент → вывод» растёт в разы
- zsh-лимит обходится (paste идёт в чат, не в терминал)
- Файлы `.tasks` версионируются в git
- Ассистент обновляет задачи через `git apply` патча
- Требует `wl-copy` (wayland) — есть в Arch по умолчанию

## Наука внутри

- **ToC**: recon — узкое место цикла, снимаем первым
- **Pareto**: 5 тегов покрывают 90% запросов
- **TDD**: `tests/test_recon_*.py` — parser, runner, formatter
- **YAGNI**: не UI-редактор .tasks, не история recon, не diff прогонов
- **Small batches**: 4 подзадачи (parser/runner/formatter/CLI) — 4 коммита

## Ссылки

- ADR-067 (Widget Control Panel)
- Правило 1 WORKING-PRINCIPLES (zsh лимит 1024)

