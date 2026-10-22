# 🛸 AuraOS — Local-First AI Companion

**AuraOS** — это автономный ИИ-компаньон, интегрированный в ядро Linux. В отличие от облачных решений (Copilot, ChatGPT), AuraOS работает **полностью локально**, обеспечивая 100% приватность данных, и использует **Model Context Protocol (MCP)** для взаимодействия с внешним миром.

## 🚀 Ключевые возможности

*   **Локальная LLM:** Работает на `qwen2.5:7b` через Ollama. Никаких утечек данных в облако.
*   **Multi-Step MCP Chaining:** Aura не просто отвечает на вопросы, она **планирует и выполняет цепочки действий** (ReAct-цикл). 
    *   *Пример:* "Найди новости про ИИ и сохрани их в файл" -> `search_news()` -> `write_file()`.
*   **Процедурная память:** Запоминает успешные сценарии ("как делать X") в SQLite с векторными эмбеддингами, ускоряя выполнение повторяющихся задач.
*   **Интеграция с инструментами (MCP Servers):**
    *   📂 **Filesystem:** Чтение, запись, поиск файлов.
    *   🗄️ **SQLite:** Выполнение SQL-запросов к базам данных.
    *   📰 **Web Search:** Поиск актуальных новостей через DuckDuckGo.
    *   🐙 **GitHub:** Чтение Issues, Pull Requests и коммитов.

## 🛠 Технологический стек

*   **Язык:** Python 3.12 (AsyncIO, Multiprocessing)
*   **LLM:** Ollama (Qwen 2.5, Nomic-Embed-Text)
*   **Протоколы:** JSON-RPC 2.0 (MCP), stdio transport
*   **Базы данных:** SQLite, ChromaDB (RAG)
*   **ОС:** Arch Linux, Systemd, X11, ALSA

## 📦 Установка и запуск

1. Установите Ollama и скачайте модели: `ollama pull qwen2.5:7b`
2. Активируйте виртуальное окружение: `source venv/bin/activate`
3. Запустите сервис: `systemctl --user start aura.service`

## 🧠 Пример работы (MCP Chaining)

```text
User: Создай файл test.txt и запиши туда Привет, мир
Aura: 🔌 [MCP Chain] Шаг 1: Вызов write_file с path: /home/user/test.txt
Aura: Файл test.txt успешно создан.
```