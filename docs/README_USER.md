# 🛸 AURA — Руководство пользователя

**Версия:** v8.2.0 «Autonomous»  
**Статус:** Active (104 агента, soak-test 24/7)  
**Платформа:** Linux (Arch, Ubuntu, Fedora)

## Что такое AURA?

AURA — автономный ИИ-компаньон, работающий **локально**. Это оркестр из **104 специализированных агентов**, которые управляют умным домом, следят за здоровьем пожилых, распознают голос, помнят контекст и контролируют систему.

**Принципы:**
- 🔒 **Приватность:** Данные (медицина, диалоги) только на вашем ПК.
- 🧠 **Локальный ИИ:** LLM qwen2.5:7b, без интернета.
- 🛠️ **Расширяемость:** Плагины, 131 ADR.
- 🛡️ **Надежность:** 24/7 мониторинг, самовосстановление.

## 🚀 Возможности

### 1. Elder-care
- **SOS-агент:** Экстренный вызов.
- **Meds:** Напоминания о лекарствах.
- **Fall:** Детектор падений.
- **FinElder:** Защита от мошенников.

### 2. Голос и Слух
- **Voice Profile (F-074):** Распознавание пользователя.
- **Ducking:** Приглушение музыки при разговоре.
- **TTS/STT:** Полный цикл без облаков.

### 3. Память (RAG)
- **ContextRecall:** Помнит события месячной давности.
- **Ledger:** Дневник и финансы.
- **VisualAnalysis:** Понимает экран.

### 4. Управление системой
- **PCControl:** Яркость, громкость, окна.
- **Browser Bridge:** Автоматизация браузера.
- **MQTT:** Home Assistant, Zigbee.

## 🏗️ Архитектура

- **Orchestrator:** Диспетчер, 104 агента.
- **Agent Registry:** Реестр с приоритетами.
- **Brain (LLM):** qwen2.5:7b-instruct-q4_K_M.
- **ChromaDB:** Векторная база RAG.
- **SQLite:** Диалоги, медицина, стресс-тесты.
- **Python 3.12** + asyncio, AppImage, systemd, MQTT.

## 🚀 Быстрый старт

### Требования
Linux, 8 GB RAM (16 GB рек.), Python 3.12, git, sqlite3, Ollama.

### Установка
```bash
git clone https://github.com/PythonVenom/aura-companion.git
cd aura-companion
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
bash install_batya.sh

## 🎙️ Тестирование голоса (обновлено 2026-10-14)

### Автотест 3 фич
./venv/bin/python scripts/test_voice.py
Ожидаемый вывод: Итого: 3/3.

### F-074: Профили голоса
python -m aura.cli check --action list
python -m aura.cli check --action show
python -m aura.cli check --action set --name medical
Доступные профили: default, medical, craft, drive, kids, dev, accessibility.

### STT / Ducking
Проверяются тем же scripts/test_voice.py (3/3).
