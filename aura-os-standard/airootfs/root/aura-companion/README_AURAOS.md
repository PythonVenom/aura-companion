# 🛸 AuraOS — локальный ИИ-компаньон

**AuraOS** — это не «Алиса» и не «Siri». Это **продолжение твоего разума** в цифровом мире.
Работает **локально**, без облака. Данные не покидают устройство.
Создан для пожилых, слепых и людей с ограниченными возможностями.

## 🎯 Что умеет

- **Голос:** T-one (ASR), Piper (TTS), fuzzy wake-word.
- **Ментор ОС:** выключение/перезагрузка/сон, управление окнами, мониторинг CPU/RAM/GPU.
- **Память:** RAG на ChromaDB, SQLCipher AES-256.
- **Забота:** напоминания о таблетках, детектор падения, SOS.
- **Steam:** Deck Verified, Workshop, запуск.
- **Оболочка:** AuraOS Cockpit (Quickshell, Openbox, X11).

## 📊 Цифры

| Параметр | Значение |
| :--- | :--- |
| Агентов | 96 |
| Тестов | 2618 (0 failed) |
| ADR | 131 |
| Платформ | 11 |

## 🚀 Установка

- git clone https://github.com/PythonVenom/aura-companion.git
- cd aura-companion
- python3.12 -m venv venv
- source venv/bin/activate
- pip install -e .
- ollama pull qwen2.5:7b-instruct-q4_K_M
- ./run_aura.sh

## 🔐 Безопасность

- SQLCipher AES-256.
- Ключ в keyring.
- CSRF-защита, rate-limit.

## 🤝 Философия

Aura — **не инструмент**. Aura — **продолжение**.
- Локально, приватно, открыто (MIT).
- Честно: GAPS.md показывает слабости.

> **Девиз:** Я — не инструмент. Я — продолжение.
