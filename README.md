# Аура

[English version →](README.en.md)

[![CI](https://github.com/PythonVenom/aura-companion/actions/workflows/ci.yml/badge.svg)](https://github.com/PythonVenom/aura-companion/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-1031-brightgreen.svg)](#)
[![Arch Linux](https://img.shields.io/badge/Arch_Linux-1793D1?logo=arch-linux&logoColor=white)](#)

**Проводник в цифровой мир** — локальный голосовой ИИ-компаньон для Linux.

Не «Алиса в терминале», а личный агент: слушает микрофон, отвечает голосом,
выполняет команды на компьютере. Всё локально — никаких облаков.

**Миссия:** сделать цифровой мир доступным для тех, кому сложно с мышью,
клавиатурой и мелкими шрифтами:

- **пожилые** — голосом: свет, ТВ, чайник, обогреватель
- **незрячие** — голосом: чаты, почта, банк, покупки
- **моторные ограничения** — голосом вместо мыши
- **ментальные особенности** — структура, память, напоминания

Подробно — [MANIFESTO.md](MANIFESTO.md).

---

**Статус:** v0.9.6-alpha · **1031 тестов** · **33 агента** · **43 ADR**
Стек: Python 3.12 · asyncio · Ollama qwen2.5:7b · T-one (ASR) · Piper (TTS) ·
ChromaDB (RAG) · PipeWire · MPRIS · Firefox WebExtension

## Быстрый старт

    git clone https://github.com/PythonVenom/aura-companion ~/aura_project
    cd ~/aura_project
    ./install.sh
    aura doctor    # проверка готовности

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

## Установка

    git clone <URL> ~/aura_project
    cd ~/aura_project
    ./install.sh

Установщик поставит системные пакеты, Python-зависимости, скачает модели
T-one и Piper, настроит systemd.

Dry-run (посмотреть, что будет сделано, без изменений):

    ./install.sh --dry-run

## После установки — вручную

1. Модели Ollama (для LLM-ответов на сложные вопросы):

    ollama pull qwen2.5:7b-instruct-q4_K_M
    ollama pull nomic-embed-text

Если места мало — можно обойтись без них. Аура потеряет умные ответы,
но базовые команды (время, погода, вкладки, музыка) будут работать.

2. VK-токен (опционально, для VK-музыки):

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

Автозапуск при входе:

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

KDE виджет — кружок в трее со статусом (ждёт / слушает / думает / говорит /
на паузе).

**Proactive:** утренний брифинг, уведомление о новом сообщении в Максе
(«Зачитать?»).

## Что НЕ умеет (пока)

- Barge-in (перебивание Ауры во время речи) — в разработке
- Windows / Mac / мобильные — план (кросс-платформа)
- Синхронизация с телефоном — план
- Telegram / VK / YouTube адаптеры — план

## Архитектура

Модульная: 33 агента, три уровня роутинга (реестр → tool_router → brain).
Диалог — через FSM (`idle` / `awaiting_command` / `pending_read`).
Proactive — через `ProactiveEngine` с триггерами и cooldown.

См. `docs/architecture.md` и `docs/adr/`.

## Документация
- [docs/manual.md](docs/manual.md) — руководство пользователя
- [docs/manual-simple.md](docs/manual-simple.md) — для начинающих
- [CONTRIBUTING.md](CONTRIBUTING.md) — как помочь
- [ARCHITECTURE.md](ARCHITECTURE.md) — архитектура


- `docs/manifesto.md` — философия, миссия, монетизация
- `docs/architecture.md` — техника
- `docs/roadmap.md` — фазы развития
- `docs/adr/` — 39 архитектурных решений (ADR-001…043)
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
- **Boosty** — https://boosty.to/aura_companion

Средства идут на: тестовое железо (N100, Strix Halo), модели, работу над кросс-платформой.

## Партнёрство

Проект открыт для:
- **Спонсорства** (модель AMD ↔ Blender: независимый разработчик + open source)
- **Грантов** на accessibility / AI / Linux
- **Железо** для тестов (AMD Strix Halo, Intel AI PC, Qualcomm ARM)

Подробности: [PARTNERSHIP.md](PARTNERSHIP.md). Контакт — через GitHub Issues с меткой `partnership`.
