# ADR-160: Deterministic Timing (P3 #159)

**Дата:** 2026-10-14  
**Статус:** Accepted  
**Контекст:** P3, космические задачи. Вдохновлено TTEthernet (SAE AS6802).

## Проблема

Агенты AURA выполняются в asyncio-цикле без гарантий по времени. Для elder-care
критично: SOS, детектор падений, напоминания о лекарствах. Нужны:
1. Гарантированный такт выполнения.
2. Измерение jitter (отклонения от идеального расписания).
3. Подсчёт пропущенных дедлайнов (missed deadlines).

## Решение

Модуль `aura/core/deterministic.py`:

- **`monotonic_ns()`** — монотонные часы (устойчивы к NTP-прыжкам).
- **`Deadline`** — абсолютный дедлайн с `is_missed()` и `remaining_ms()`.
- **`JitterStats`** — mean/max/min/p95 для jitter в мс.
- **`DeterministicScheduler`** — fixed-tick scheduler с `run(task, iterations)`.

## Обоснование

- **Почему monotonic, а не time.time():** `time.time()` может прыгнуть назад
  при NTP-синхронизации. `time.monotonic_ns()` гарантирует неубывание.
- **Почему отдельный класс, а не asyncio.sleep:** нужны метрики jitter и missed,
  которых нет в стандартном event loop.
- **Почему tick_ms в конструкторе:** гибкость — 10 мс для аудио, 100 мс для
  напоминаний, 1000 мс для фоновых задач.

## Последствия

**Плюсы:**
- Гарантии по дедлайнам для критичных агентов.
- Метрики jitter → в stress.db для мониторинга.
- Основа для TMR (#157) — репликация с синхронным тактом.

**Минусы:**
- Python-планировщик не hard-real-time (GIL, планировщик ОС).
- Для жесткого реального времени нужен C/Rust или RT-патч ядра.

## Связи

- **Предшественники:** #95 (stress-test), #142 (Naptime), #152 (Watchdog).
- **Последователи:** #157 (TMR), #158 (Radiation-tolerant storage).
- **Тесты:** `tests/test_deterministic.py` (8 тестов, 100% pass).

## Ссылки

- SAE AS6802 (TTEthernet).
- ISTQB: Deterministic testing.
