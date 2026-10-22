# ADR-078: Universal Installer + Hardware Profiles

**Дата:** 2026-10-02
**Статус:** Принято

## Контекст

Цель: батя (Linux Mint/Ubuntu) ставит Aura **одной командой** через
`curl | bash`, без терминала, без ручной настройки.

Существующий `install.sh` работает только на Arch (186 строк).
Остальные 8 файлов — stubs: скачивают venv, но не T-one, не Piper,
не systemd, не Ollama. Батя не поставит.

Проблема железа: разные машины — от 4 ГБ RAM (слабый ноут) до 31 ГБ
(мощная станция). qwen2.5:7b требует ~8 ГБ — не влезет на слабом.

## Решение

### 1. `contrib/aura-detect.sh`
Определяет RAM, CPU cores, GPU, выбирает профиль:
- `minimal` (≤4 ГБ): LLM off, AURA_BRAIN=0
- `low` (4–8 ГБ): qwen2.5:3b
- `medium` (8–16 ГБ): qwen2.5:7b
- `full` (>16 ГБ): qwen2.5:7b + GPU

### 2. `install_universal.sh`
Универсальный installer для:
- Debian/Ubuntu/Mint (apt)
- Fedora/RHEL/CentOS (dnf)
- Arch/Manjaro (pacman)
- Alpine (apk)
- macOS (brew)

Что делает:
1. Detect OS (через /etc/os-release)
2. Detect hardware (aura-detect.sh)
3. Выбор LLM по профилю
4. apt/dnf/pacman/brew install (system deps)
5. Python venv + pip install -e .
6. Скачивание T-one (~144 МБ) + Piper voice (~63 МБ)
7. ollama pull нужной модели (по профилю)
8. systemd user unit + drop-in с AURA_PROFILE
9. config_wizard (first-run)

### 3. Использование

Батя (Ubuntu/Mint):
    curl -fsSL https://raw.githubusercontent.com/PythonVenom/aura-companion/v1.1.0/install_universal.sh | bash

Dry-run (проверить без изменений):
    ./install_universal.sh --dry-run

## YAGNI

- Не пишем GUI installer
- Не пишем .deb/.rpm/.msi — пока curl|bash
- Не пишем поддержку BSD
- Не тестируем на всех ОС сразу (ToC: Ubuntu первым)

## ToC

Узкое место — батя на Ubuntu. Значит Ubuntu первым тестируется.
Проверка на Mint VM (4 ГБ → minimal, 8 ГБ → medium).

## Открытые вопросы

1. `ollama pull` может занять 5–10 мин (user ждёт)
2. Если у user нет sudo — installer падает (graceful?)
3. WSL2: работает, но mic через WSLg (TBD)
4. macOS: brew есть, но systemd — нет (launchd TBD)

## Последствия

- Одна команда → Aura работает (15 мин)
- Профили железа автоматически выбирают LLM
- 9 старых install_*.sh — deprecated (можно удалить позже)

## Ссылки

- ADR-019 Installation Experience (три уровня)
- ADR-021 Flash-install (USB для бабушек)
- ADR-017 Platform Abstraction Layer
