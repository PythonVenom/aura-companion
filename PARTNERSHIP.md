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

- **Python 3.12** + asyncio, модульная архитектура (33 агента)
- **Локальный LLM:** Ollama (qwen2.5:7b) — работает offline
- **ASR:** T-one (streaming, русский)
- **TTS:** Piper (локальный синтез)
- **RAG:** ChromaDB — память диалогов
- **Audio:** PipeWire + WirePlumber + BargeIn (VAD)
- **DE:** KDE Plasma 6, MPRIS, systemd --user
- **Browser:** Firefox WebExtension + native messaging
- **39 ADR** — архитектурные решения документированы

## Текущий статус

| Метрика | Значение |
|---|---|
| Тестов | **707** (pytest) |
| Агентов | **26** |
| ADR | **16** |
| Коммитов | 156 |
| Лицензия | MIT |
| Статус | v0.9.6-alpha, публичный релиз 27.09.2026 |

## Почему с AMD

**Портфолио:** Aura — работающий кейс **локального ИИ без облака**. Это то, что AMD продвигает через Ryzen AI и Strix Halo.

**Технологически:**
- Локальные LLM (7B параметров) — на CPU и GPU
- Голосовой цикл в реальном времени (ASR + LLM + TTS)
- Целевая платформа — Linux, Arch, KDE
- Готов к бенчмаркам на ROCm

**Стратегически:**
- **Accessibility-first** — редкая ниша, высокая социальная значимость
- **Open Source (MIT)** — модель Blender ↔ AMD
- **Кросс-платформенный roadmap** — Arch → Ubuntu → Windows → Android
- **TinyML** в перспективе — от смартфона до микроволновки

## Что ищу

- **Спонсорство:** модель AMD ↔ Blender — независимый разработчик + open source
- **Железо:** Strix Halo для тестирования ROCm и локальных LLM
- **Гранты:** accessibility, AI, Linux ecosystem
- **Интеграции:** AT-SPI, MCP, кастомные коробки

## Roadmap (публичный)

- **Q4 2026:** Arch Linux до 100% (24/7 стабильность, бета)
- **Q1 2027:** Ubuntu/Debian, ADR-017 Platform Abstraction
- **Q2 2027:** Windows (WASAPI, WinAPI)
- **Q3 2027:** Android (Termux → Kotlin)
- **2028+:** TinyML (ESP32), macOS

## Аналоги для сравнения

| Проект | Что сделал | Почему Aura отличается |
|---|---|---|
| Mycroft AI | Open-source голосовой ассистент | Aura — accessibility-first, локальный LLM, Arch |
| Rhasspy | Голосовые команды для Home Assistant | Aura — для компьютера, а не для умного дома |
| Leon AI | Personal assistant | Aura — российский, русский ASR/TTS из коробки |
| Home Assistant Voice | Умный дом | Aura — рабочий стол, мессенджеры, браузер |

**Отличие:** Aura — **не «умная колонка»**, а **проводник в цифровой мир** для тех, кому это трудно.

## Медиа и материалы

- README: [github.com/PythonVenom/aura-companion](https://github.com/PythonVenom/aura-companion)
- Манифест: [MANIFESTO.md](MANIFESTO.md)
- Архитектура: [docs/architecture.md](docs/architecture.md)
- ADR: [docs/adr/](docs/adr/)

**Демо-видео и бенчмарки** — готовятся. Будут добавлены в ближайшие недели.

## Контакт

- **GitHub Issues:** метка `partnership`
- **Email:** будет добавлен в ближайшие дни
- **Telegram:** будет добавлен в ближайшие дни

---

*Aura — свет, который ведёт. Не за тебя. С тобой.*
