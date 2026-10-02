# Aura

[English version →](README.en.md)

[![CI](https://github.com/PythonVenom/aura-companion/actions/workflows/ci.yml/badge.svg)](https://github.com/PythonVenom/aura-companion/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-1271-brightgreen.svg)](#)
[![Arch Linux](https://img.shields.io/badge/Arch_Linux-1793D1?logo=arch-linux&logoColor=white)](#)

▶️ [Demo (90 sec, test run)](https://github.com/PythonVenom/aura-companion/releases/tag/demo-test-run)

**Голосовой слой над ОС.** Локально. Open source. Без облака.

Слушает микрофон, отвечает голосом, выполняет команды на компьютере. Всё локально — никаких облаков.

**Статус:** v1.0.0 · **1271 тест** · **37 агентов** · **50 ADR**
Стек: Python 3.12 · asyncio · Ollama qwen2.5:7b · T-one (ASR) · Piper (TTS) · ChromaDB (RAG) · PipeWire · MPRIS · Firefox WebExtension

## Быстрый старт

    git clone https://github.com/PythonVenom/aura-companion ~/aura_project
    cd ~/aura_project
    ./install.sh
    aura doctor    # проверка готовности

**Для первого запуска — Arch Linux.** Остальные — экспериментальные.

Подробно:
- [docs/manual.md](docs/manual.md) — полный справочник
- [docs/manual-simple.md](docs/manual-simple.md) — для начинающих
- [docs/craft-onboarding.md](docs/craft-onboarding.md) — для мастеров (ЧПУ, 3D, дизайн)

## Требования

- **ОС:** Arch Linux (или производные)
- **Оборудование:** микрофон + колонки/наушники
- **Место:** ~5 ГБ (модели T-one, Piper, Ollama)
- **Python:** 3.11+
- **Опционально:** PipeWire (для AEC / чистого слуха)

## Железо

**Текущий прототип:**

- **CPU:** Intel Core i7-8750H @ 2.20GHz (6 ядер, 12 потоков)
- **RAM:** 31 GiB
- **GPU:** NVIDIA GeForce GTX 1070 Mobile (8 GB VRAM) + Intel UHD Graphics 630
- **ОС:** Arch Linux + Plasma (Wayland)
- **Аудио:** PipeWire
- **Архитектура:** x86_64

## Установка

**Ubuntu / Debian / Mint / Fedora (универсально):**

    curl -fsSL https://raw.githubusercontent.com/PythonVenom/aura-companion/master/install_universal.sh | bash

**Arch Linux:**

    git clone <URL> ~/aura_project
    cd ~/aura_project
    ./install.sh

Установщик поставит системные пакеты, Python-зависимости, скачает модели T-one и Piper, настроит systemd.

Dry-run (посмотреть, что будет сделано, без изменений):

    ./install.sh --dry-run

## После установки — вручную

1. Модели Ollama:

    ollama pull qwen2.5:7b-instruct-q4_K_M
    ollama pull nomic-embed-text

2. VK-токен (опционально):

    echo 'ТВОЙ_ТОКЕН' > ~/aura_project/vk_token.txt
    chmod 600 ~/aura_project/vk_token.txt

3. Hotkey паузы (опционально, KDE Plasma):

System Settings -> Shortcuts -> Add Application -> Aura Pause
Назначить сочетание: Ctrl+Alt+P или CapsLock+F8

## Запуск

    systemctl --user start aura.service

Логи:

    journalctl --user -u aura.service -f

Остановка:

    systemctl --user stop aura.service

Автозапуск:

    systemctl --user enable aura.service

## Что умеет

Голосовые команды — скажи «Аура» и команду:

- «Аура, который час» — время
- «Аура, какая погода в Москве» — погода
- «Аура, расскажи историю про космос» — LLM отвечает
- «Аура, какие вкладки открыты» — Firefox bridge
- «Аура, найди вкладку макс» — переключение
- «Аура, открой ВК» — фокус на вкладку или открытие
- «Аура, следующий рабочий стол» — переключение столов (KDE)
- «Аура, приглуши музыку» — ducking
- «Аура, включи музыку» / «пауза» / «следующий» — локальная музыка (VLC)
- Макс: чтение и отправка сообщений голосом (Макс → Аура через pull)

Горячая клавиша — пауза/возобновление прослушки.

KDE виджет — кружок в трее со статусом (ждёт / слушает / думает / говорит / на паузе).

**Proactive:** утренний брифинг, уведомление о новом сообщении в Максе («Зачитать?»).

## Архитектура

Модульная: 37 агентов, три уровня роутинга (реестр → tool_router → brain). Диалог — через FSM (`idle` / `awaiting_command` / `pending_read`). Proactive — через `ProactiveEngine` с триггерами и cooldown.

См. `docs/architecture.md` и `docs/adr/`.

## Документация

- [docs/manual.md](docs/manual.md) — руководство пользователя
- [docs/manual-simple.md](docs/manual-simple.md) — для начинающих
- [CONTRIBUTING.md](CONTRIBUTING.md) — как помочь
- [ARCHITECTURE.md](ARCHITECTURE.md) — архитектура
- `docs/adr/` — 50 архитектурных решений (ADR-001…052)
- `JOURNAL.md` — хроника

## Лицензия

MIT — см. `LICENSE`.

## Автор

pythonvenom (один разработчик + ИИ-ассистент).

## Связь

- **Баги, идеи, вопросы:** [GitHub Issues](https://github.com/PythonVenom/aura-companion/issues)
- **Обсуждения:** [GitHub Discussions](https://github.com/PythonVenom/aura-companion/discussions)
- **Telegram:** [@Pyth0nVen0m](https://t.me/Pyth0nVen0m)
- **YouTube:** [@dev1nr0ss36](https://youtube.com/@dev1nr0ss36)
- **MAX:** [max.ru/u/32480561](https://max.ru/u/32480561)
- **Полный список контактов:** [CONTACTS.md](CONTACTS.md)

## Поддержать проект

Aura — независимый open-source проект. Всё локально, без подписок и рекламы. Если проект помогает — можно поддержать разработку:

- **CloudTips** — https://pay.cloudtips.ru/p/9ce9959c (0% для донатора)
- **Boosty** — https://boosty.to/aura_companion
- **DonationAlerts** — <вписать ссылку>

**Куда идут средства:**

- **Жизнь:** врачи, лекарства, питание. Разработчик имеет инвалидность (опорно-двигательный аппарат) и работает над проектом 10 часов в день.
- **Тестовое железо:** для кросс-платформенных тестов.
- **Работа над Aura:** кросс-платформенный слой.

Каждый донат = больше времени на код.
