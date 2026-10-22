# Aura — Partnership Overview

> Локальный голосовой ИИ-компаньон для Linux.
> Accessibility-first. Open Source (MIT). Arch Linux.

**Контакт:** GitHub Issues с меткой `partnership` · [PythonVenom/aura-companion](https://github.com/PythonVenom/aura-companion)

---

## Что такое Aura

Aura — голосовой ассистент, который делает цифровой мир доступным для людей, кому сложно с мышью, клавиатурой и мелкими шрифтами:

- **Пожилые** — голосом: свет, музыка, звонки, ТВ
- **Незрячие** — голосом: чаты, почта, банк
- **Моторные ограничения** — голосом вместо мыши
- **Ментальные особенности** — структура, напоминания

**Всё локально.** Никаких облаков, никаких подписок, никакой слежки.

## Технологический стек

- **Python 3.12** + asyncio, модульная архитектура (105 агентов)
- **Локальный LLM:** Ollama (qwen2.5:7b) — работает offline
- **ASR:** T-one (streaming, русский)
- **TTS:** Piper (локальный синтез)
- **RAG:** ChromaDB — память диалогов
- **Audio:** PipeWire + WirePlumber + BargeIn (VAD)
- **DE:** KDE Plasma 6, MPRIS, systemd --user
- **Browser:** Firefox WebExtension + native messaging + CDP
- **131 ADR** — архитектурные решения документированы

## Текущий статус

| Метрика | Значение |
|---|---|
| Тестов | 2450+ (pytest) |
| Агентов | 105 |
| ADR | 131 |
| Коммитов | 220+ |
| Лицензия | MIT |
| Статус | v8.2.0 «Autonomous», public release 13.10.2026 |

## Что ищу

- **Гранты:** accessibility, AI, Linux ecosystem
- **Интеграции:** AT-SPI, MCP, кастомные коробки
- **Железо:** для тестирования локальных LLM

## Как собрать самому (5 минут)

Всё готово — исходники в открытом доступе. Любой может собрать Aura.

### Обычная установка

1. Клонировать:
   git clone https://github.com/PythonVenom/aura-companion.git
   cd aura-companion

2. Установить (авто-определит ОС: Arch / Ubuntu / Debian / Fedora / Alpine / macOS):
   ./install_universal.sh

3. Запустить:
   systemctl --user start aura.service

### Для elder-care (батя)

   ./install_batya.sh

Профиль elder: без LLM, голос медленнее, автостарт.
Скрипт сам поставит пакеты, создаст venv, скачает голос, настроит systemd.

### Свой Live ISO

   ./aura-make-iso.sh

Скрипт соберёт archiso-профиль. ISO появится в aura-os/out/.
Установка через dd — команда будет показана после сборки.

### Свой portable на флешку

   ./aura-usb.sh /mnt/usb --download-models

Создаст структуру на флешке: aura-project / aura-cache / aura-config / aura-models.
Вставил в чужой ПК — заработало.

### Проверки

Все зависимости в docs/SBOM.json (CycloneDX 1.5).
Стандарты: 12-Factor App, SemVer 2.0, OWASP Top 10.

## Аналоги для сравнения

| Проект | Что сделал | Почему Aura отличается |
|---|---|---|
| Mycroft AI | Open-source голосовой ассистент | Aura — accessibility-first, локальный LLM, Arch |
| Rhasspy | Голосовые команды для Home Assistant | Aura — для компьютера, а не для умного дома |
| Leon AI | Personal assistant | Aura — российский, русский ASR/TTS из коробки |
| Home Assistant Voice | Умный дом | Aura — рабочий стол, мессенджеры, браузер |

**Отличие:** Aura — не «умная колонка», а проводник в цифровой мир для тех, кому это трудно.

## Медиа и материалы

- README: github.com/PythonVenom/aura-companion
- Манифест: MANIFESTO.md
- Архитектура: docs/architecture.md
- ADR: docs/adr/
- SBOM: docs/SBOM.json

## Контакт

- **GitHub Issues:** метка partnership
- **Telegram:** @Pyth0nVen0m

---

*Aura — свет, который ведёт. Не за тебя. С тобой.*
