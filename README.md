# Aura — Local Family AI Companion

> A local-first, family-oriented AI that speaks, acts, and remembers.
> Not a voice assistant — a world mediator.

![Tests](https://img.shields.io/badge/tests-1339_passed-green)
![Evals](https://img.shields.io/badge/evals-44%2F44_100%25-green)
![ADR](https://img.shields.io/badge/ADR-99-blue)
![Handlers](https://img.shields.io/badge/handlers-22-orange)
![Routes](https://img.shields.io/badge/routes-7-purple)

## What is Aura

Aura is a **local, family-focused AI mediator** between people and the digital world:

- Voice-first (ASR + TTS, ru)
- Local LLM (Ollama, no cloud)
- 22 capability handlers (music / time / app / browser / power / control / care / journal)
- Behavior-tree router (7 leaves)
- i18n: ru / en / zh / es
- 99 ADRs — design decisions documented
- 1339 unit tests + 44 golden evals
- Honeypots, threat model, backup

## Quick start

    git clone https://github.com/PythonVenom/aura-companion.git
    cd aura-companion
    python -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    python -m aura

## Philosophy

- **Local-first**: your data never leaves your machine
- **Family-oriented**: care agent, voice journal, elder-friendly
- **Plasma-adaptive**: idempotent patches, ADR-after-code, release gates
- **Antifragile**: every red hole is harvested into a green strength

## Languages

- [English](README.md)
- [Русский](README.ru.md)
- [中文](README.zh.md) (soon)
- [Español](README.es.md) (soon)

## License

MIT
