# Aura — локальный семейный ИИ-компаньон

> Локальный, семейный ИИ, который говорит, действует и помнит.
> Не голосовой ассистент — прослойка мира.

![Tests](https://img.shields.io/badge/tests-1339_passed-green)
![Evals](https://img.shields.io/badge/evals-44%2F44_100%25-green)
![ADR](https://img.shields.io/badge/ADR-99-blue)
![Handlers](https://img.shields.io/badge/handlers-22-orange)
![Routes](https://img.shields.io/badge/routes-7-purple)

## Что такое Aura

Aura — **локальный семейный ИИ-медиатор** между человеком и цифровым миром:

- Голос (ASR + TTS, ru)
- Локальный LLM (Ollama, без облака)
- 22 handler-а (music / time / app / browser / power / control / care / journal)
- Behavior Tree роутер (7 листьев)
- i18n: ru / en / zh / es
- 99 ADR — все решения задокументированы
- 1339 unit-тестов + 44 golden evals
- Honeypots, threat model, backup

## Быстрый старт

    git clone https://github.com/PythonVenom/aura-companion.git
    cd aura-companion
    python -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    python -m aura

## Философия

- **Локальность**: данные не покидают машину
- **Семейность**: care-агент, голосовой дневник, для старших
- **Плазма**: идемпотентные патчи, ADR после кода, release gate
- **Антихрупкость**: каждая красная дыра становится зелёным козырем

## Языки

- [English](README.md)
- [Русский](README.ru.md)

## Лицензия

MIT
