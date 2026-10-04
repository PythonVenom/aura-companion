# Aura — Voice Guide to the Digital World

> A local-first AI companion. Not a voice assistant — a world mediator.
> For elderly, blind, motor-impaired, and everyone who struggles with the digital world.

[![CI](https://github.com/PythonVenom/aura-companion/actions/workflows/ci.yml/badge.svg)](https://github.com/PythonVenom/aura-companion/actions/workflows/ci.yml)
![Tests](https://img.shields.io/badge/tests-1403_passed-green)
![ADR](https://img.shields.io/badge/ADR-115-blue)
![Agents](https://img.shields.io/badge/agents-48-orange)
![Handlers](https://img.shields.io/badge/handlers-22-purple)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

<video src="docs/demo.mp4" autoplay loop muted playsinline width="600"></video>

## Why Aura exists

I am pythonvenom. I started Aura for **myself** — I have my own difficulties
with the digital world — and for **elderly people with disabilities**.

The digital world has become mandatory: bank, calls, government, doctors.
But entering it requires a mouse, keyboard, tiny fonts, a dozen clicks,
and memory for passwords. For millions, this is a **barrier**:

- Elderly — mouse is an enemy, font is a test
- Blind — screen readers are complex, sites are not adapted
- Motor impairments — the cursor does not obey
- Mental specifics — structure is lost, memory fails

**Aura answers with voice.** One tool everyone has. Locally. No cloud, no subscriptions, no surveillance.

> Not "for the disabled." For **everyone** who finds the digital world hard.
> That is billions of people.

## What Aura is

- **Voice-first** — T-one streaming ASR (Russian) + Piper TTS with ruaccent
- **Local LLM** — Ollama qwen2.5:7b, works offline
- **48 agents** — time / music / browser / power / care / journal / ...
- **22 dispatcher handlers**
- **RAG memory** — ChromaDB, remembers dialogues
- **115 ADRs** — every design decision documented
- **1403 unit tests** — green
- **Works on**: KDE / GNOME / XFCE / Cinnamon / MATE + X11 / Wayland

## Quick start

### Способ 1: из исходников

    git clone https://github.com/PythonVenom/aura-companion.git
    cd aura-companion
    python -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    python -m aura

### Способ 2: AppImage (портативно, без установки)

    chmod +x Aura-*.AppImage
    ./Aura-*.AppImage

### Способ 3: Docker

    cd packaging/docker
    docker compose up -d

### Способ 4: AUR (Arch)

    yay -S aura-companion

## 10 осей проекта (карта Aura v7.2 → v8.0)

| # | Ось | Цель | Сейчас | Статус |
|---|---|---|---|---|
| 1 | Функции (elder care) | 160 | 25 | 🟡 16% |
| 2 | Окружения (DE × WM) | 120 | 72 | 🟡 60% |
| 3 | Дистрибуция (форматы) | 30 | 6 | 🟡 20% |
| 4 | Архитектуры | 13 | 3 | 🟡 23% |
| 5 | Локали | 50 | 8 | 🟡 16% |
| 6 | Устройства (TV, кнопки) | 20 | 2 | 🔴 10% |
| 7 | Протоколы (Matter, MQTT) | 12 | 1 | 🔴 8% |
| 8 | Медицина | 12 | 0 | 🔴 0% |
| 9 | X5 (Audio LLM, twin) | 12 | 0 | 🔴 0% |
| 10 | Automotive | 10 | 0 | 🔴 0% |

**Цель v8.0 (Arch 100%):** закрыть 8 из 10 осей на 10/10.

### Roadmap (4 фазы)

- **Фаза I — Foundation (4 мес):** v7.2-v8.0 → Arch 100% (TRL 7)
- **Фаза II — Automotive entry (1-2 мес):** v9.0 → CarPlay + Android Auto
- **Фаза III — Mars-grade (6 мес):** v10.x → Formal + self-healing
- **Фаза IV — Automotive deep (год 2-3):** v11-v13 → AAOS, CAN-bus, OEM

## Philosophy

1. **Local-first.** Everything runs on your machine. Your data is yours.
2. **Simplicity as respect.** Not a "convenient interface", but an interface that **requires no learning**.
3. **The name is yours.** By default "Aura". But the user can rename to "Katya", "Marusya", "Grandpa" — like a family member.
4. **Extensibility as philosophy.** Not replacing a human — connecting them to the world.
5. **Accessibility is the core**, not a bolt-on feature.

## Who it is for

- **Elderly** — voice control: light, TV, kettle, calls
- **Blind and low-vision** — voice: chats, mail, bank, shopping
- **Motor impairments** — voice instead of mouse
- **Mental specifics** — structure, memory, reminders
- **Anyone** who wants local-first, no-cloud AI

## What works

- Voice input (T-one streaming ASR, Russian)
- Voice output (Piper + ruaccent stress marks)
- 48 agents: time, music, browser, apps, power, care, journal
- RAG memory (dialogues persist)
- Echo filter, graceful SIGTERM
- Tier 0 fast-path
- env/ layer: KDE / GNOME / XFCE / Cinnamon / MATE + X11 / Wayland

## What does NOT work yet (early access)

- Elder profile on Linux Mint — **in testing**
- install.sh — build from source for now
- Flatpak / AUR / PyPI — not published yet
- Android / iOS / Windows — roadmap only

## Support the project

Aura is non-commercial open source. If it helps you or your loved ones:

- ⭐ Star on GitHub
- 🐛 Issue or PR (code, docs, translations)
- 💰 [CloudTips](https://pay.cloudtips.ru/p/9ce9959c) · [Boosty](https://boosty.to/aura_companion)
- 🤝 [Partnership](PARTNERSHIP.md)

Donations go to: CI runners, test devices, domains.

## Languages

- [English](README.md)
- [Русский](README.ru.md)

## License

MIT — see [LICENSE](LICENSE).
