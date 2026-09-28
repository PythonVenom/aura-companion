# Aura

[![CI](https://github.com/PythonVenom/aura-companion/actions/workflows/ci.yml/badge.svg)](https://github.com/PythonVenom/aura-companion/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-977-brightgreen.svg)](#)
[![Arch Linux](https://img.shields.io/badge/Arch_Linux-1793D1?logo=arch-linux&logoColor=white)](#)

**A guide into the digital world** — a local voice AI companion for Linux.

Not "Alexa in a terminal". A personal agent: listens to the microphone,
answers with voice, executes commands on your computer. **Everything local —
no cloud, no telemetry, no tracking.**

**Mission:** make the digital world accessible to those who struggle with
mouse, keyboard, and small fonts:

- **elderly** — voice control: lights, TV, kettle, heater
- **blind** — voice: chats, email, banking, shopping
- **motor impairments** — voice instead of mouse
- **cognitive differences** — structure, memory, reminders

Read more — [MANIFESTO.md](MANIFESTO.md).

---

**Status:** v0.9.0-alpha · **977 tests** · **26 agents** · **16 ADRs**
Stack: Python 3.12 · asyncio · Ollama qwen2.5:7b · T-one (ASR) · Piper (TTS)
· ChromaDB (RAG) · PipeWire · MPRIS · Firefox WebExtension

## Requirements

- **OS:** Arch Linux (or derivatives)
- **Hardware:** microphone + speakers/headphones
- **Space:** ~5 GB (T-one, Piper, Ollama models)
- **Python:** 3.11+
- **Optional:** PipeWire (for AEC / clean audio)

## Installation

    git clone <URL> ~/aura_project
    cd ~/aura_project
    ./install.sh

The installer sets up system packages, Python deps, downloads T-one and
Piper models, configures systemd.

Dry-run (see what will happen, no changes):

    ./install.sh --dry-run

## After installation — manual steps

1. Ollama models (for LLM responses to complex questions):

    ollama pull qwen2.5:7b-instruct-q4_K_M
    ollama pull nomic-embed-text

If short on space — can skip. Aura will lose smart answers but basic
commands (time, weather, tabs, music) will work.

2. VK token (optional, for VK music):

    echo 'YOUR_TOKEN' > ~/aura_project/vk_token.txt
    chmod 600 ~/aura_project/vk_token.txt

3. Pause hotkey (optional, KDE Plasma):

System Settings -> Shortcuts -> Add Application -> Aura Pause
Assign: Ctrl+Alt+P or CapsLock+F8

## Running

    systemctl --user start aura.service

Logs:

    journalctl --user -u aura.service -f

Stop:

    systemctl --user stop aura.service

Auto-start on login:

    systemctl --user enable aura.service

## What it can do

Voice commands — say "Aura" and the command:

- "Aura, what time is it" — time
- "Aura, weather in Moscow" — weather
- "Aura, tell a story about space" — LLM answers
- "Aura, what tabs are open" — Firefox bridge
- "Aura, find MAX tab" — switch
- "Aura, open VK" — focus tab or open
- "Aura, next desktop" — KDE desktop switch
- "Aura, duck the music" — volume ducking
- "Aura, play music" / "pause" / "next" — local music (VLC)
- MAX: read and send messages by voice (MAX → Aura via pull)

Hotkey — pause/resume listening.

KDE widget — tray indicator with status (idle / listening / thinking /
speaking / paused).

**Proactive:** morning briefing, notification about new MAX message
("Should I read?"), reminder about unanswered messages.

## What it CANNOT do (yet)

- Barge-in (interrupting Aura mid-speech) — in development
- Windows / Mac / mobile — planned (cross-platform)
- Phone sync — planned
- Telegram / VK / YouTube adapters — planned

## Architecture

Modular: 26 agents, three routing levels (registry → tool_router → brain).
Dialogue via FSM (`idle` / `awaiting_command` / `pending_read` /
`awaiting_reply`). Proactive via `ProactiveEngine` with triggers and cooldown.

See [docs/architecture.md](docs/architecture.md) and [docs/adr/](docs/adr/).

## Benchmarks

Baseline on old hardware (Intel Coffee Lake-H + NVIDIA GTX 1070M, 2016):

- **LLM:** ~48 tok/s (qwen2.5:7b Q4)
- **ASR:** RTF 0.058 (17× real-time) — T-one streaming CTC
- **TTS:** ~300 ms synth — Piper
- **End-to-end:** ~1 sec per short command

**Expected on AMD Strix Halo:** 5–10× faster (250+ tok/s), 32B models
fit in unified memory. See [benchmarks/BENCHMARKS.md](benchmarks/BENCHMARKS.md).

## Documentation

- [MANIFESTO.md](MANIFESTO.md)
- [docs/manual.md](docs/manual.md) — user manual (RU)
- [docs/manual-simple.md](docs/manual-simple.md) — beginner guide (RU) — philosophy, mission
- [PARTNERSHIP.md](PARTNERSHIP.md) — for companies and sponsors
- [docs/architecture.md](docs/architecture.md) — technical
- [docs/adr/](docs/adr/) — 16 architectural decisions (ADR-001…016)

## Contact

- **Bugs, ideas, questions:** [GitHub Issues](https://github.com/PythonVenom/aura-companion/issues)
- **Discussions:** [GitHub Discussions](https://github.com/PythonVenom/aura-companion/discussions)
- **Telegram:** [@Pyth0nVen0m](https://t.me/Pyth0nVen0m)
- **YouTube:** [@dev1nr0ss36](https://youtube.com/@dev1nr0ss36)
- **Full contact list:** [CONTACTS.md](CONTACTS.md)

## Support the project

Aura is an independent open-source project. Everything local, no
subscriptions, no ads. If the project helps — you can support development:

- **CloudTips** — https://pay.cloudtips.ru/p/9ce9959c
- **Boosty** — https://boosty.to/aura_companion

Funds go to: test hardware (N100, Strix Halo), models, cross-platform work.

## Partnership

Project is open for:
- **Sponsorship** (AMD ↔ Blender model: independent developer + open source)
- **Grants** for accessibility / AI / Linux
- **Hardware** for testing (AMD Strix Halo, Intel AI PC, Qualcomm ARM)

Details: [PARTNERSHIP.md](PARTNERSHIP.md). Contact — via GitHub Issues with
`partnership` label.

## License

MIT — see [LICENSE](LICENSE).

## Author

PythonVenom (one developer + AI assistant).

---

*Aura — the light that guides. Not for you. With you.*
