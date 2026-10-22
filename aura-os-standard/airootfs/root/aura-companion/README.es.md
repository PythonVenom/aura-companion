# Aura — Compañero familiar de IA local

> Una IA local-first, orientada a la familia, que habla, actúa y recuerda.
> No es un asistente de voz — **un mediador del mundo**.

![Tests](https://img.shields.io/badge/tests-1339_passed-green)
![Evals](https://img.shields.io/badge/evals-44%2F44_100%25-green)
![ADR](https://img.shields.io/badge/ADR-99-blue)
![Handlers](https://img.shields.io/badge/handlers-22-orange)
![Routes](https://img.shields.io/badge/routes-7-purple)

## Qué es Aura

Aura es un **mediador familiar de IA local** entre las personas y el mundo digital:

- Voz primero (ASR + TTS, ru)
- LLM local (Ollama, sin nube)
- 22 handlers (music / time / app / browser / power / control / care / journal)
- Router de árbol de comportamiento (7 hojas)
- i18n: ru / en / zh / es
- 99 ADRs — decisiones documentadas
- 1339 tests + 44 golden evals
- Honeypots, threat model, backup

## Inicio rápido

    git clone https://github.com/PythonVenom/aura-companion.git
    cd aura-companion
    python -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    python -m aura

## Filosofía

- **Local-first**: tus datos nunca salen de tu máquina
- **Familiar**: agente de cuidado, diario de voz, para mayores
- **Plasma-adaptativo**: parches idempotentes, ADR tras código, release gates
- **Antifrágil**: cada agujero rojo se convierte en una fortaleza verde

## Idiomas

- [English](README.md)
- [Русский](README.ru.md)
- [中文](README.zh.md)
- [Español](README.es.md)

## Licencia

MIT
