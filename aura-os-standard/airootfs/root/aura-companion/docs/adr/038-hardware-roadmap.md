# ADR-038: Hardware Roadmap

**Дата:** 2026-09-28
**Статус:** Проект
**Связано:** strategy-2026.md, ADR-035

## Контекст

Aura живёт на разном железе: от Pi Zero до Strix Halo.
Нужна единая стратегия платформ.

## Решение

**4 класса устройств:**

### 1. Lite (Lite-режим, без LLM)

| Устройство | RAM | Цена | Сегмент |
|---|---|---|---|
| Raspberry Pi Zero 2W | 512 МБ | 2000 ₽ | Aura Lite |
| Orange Pi Zero 3 | 1 ГБ | 3000 ₽ | Aura Lite |
| Старый ноут | 2 ГБ | 0 ₽ (втор. жизнь) | Aura Lite |

### 2. Standard (7B LLM)

| Устройство | RAM | Цена | Сегмент |
|---|---|---|---|
| **Intel N100 mini-PC** | 16 ГБ | 15k ₽ | **Aura Box** |
| Raspberry Pi 5 | 8 ГБ | 12k ₽ | Aura Box |
| Refurbished i5 (8-10 gen) | 16 ГБ | 20k ₽ | DIY |

### 3. Pro (13-32B LLM)

| Устройство | RAM/VRAM | Цена | Сегмент |
|---|---|---|---|
| **AMD Strix Halo (Ryzen AI Max 395)** | 128 ГБ unif. | 150k ₽ | **Aura Studio** |
| Mac Mini M4 Pro | 48 ГБ unif. | 200k ₽ | Aura Studio (macOS) |
| NVIDIA RTX 4090 + i9 | 24 ГБ VRAM | 400k ₽ | Aura Studio (DIY) |

### 4. Distributed (несколько коробок)

См. ADR-039.

## Позиционирование

| Продукт | Аудитория | Цена | Лицензия |
|---|---|---|---|
| **Aura Lite** | Пожилые, незрячие, базовая автоматизация | Free (SW) + 5k ₽ (HW) | MIT |
| **Aura Box** | Дом, офис, accessibility | 15-30k ₽ | MIT + BSL Pro |
| **Aura Studio** | Медицина, бухгалтерия, малые мастерские | 150-300k ₽ | BSL Pro |
| **Aura Craft Box** | ЧПУ, мастерские | 50-80k ₽ (промышл. корпус) | BSL Pro |

## Партнёрства

- **AMD** — Strix Halo как reference (ADR-035, Blender-модель)
- **Intel** — N100 как entry-level (NUC for Business)
- **Raspberry Pi Foundation** — accessibility-миссия совпадает
- **Qualcomm** — Snapdragon X Elite (ARM64 Windows, будущее)

## Сроки

| HW | Q | Комментарий |
|---|---|---|
| N100 mini-PC | Q1 2026 | Тест на 10 пользователях |
| Pi 5 | Q1 2026 | Параллельно |
| Strix Halo | Q2-Q3 2026 | Когда AMD ответит |
| ESP32 micro-Aura | 2027 | Wake-word only |

## Что НЕ делаем

- Своё железо (N100 у InnoVista дёшево и достаточно)
- Production (слишком сложно, YAGNI)
- Собственные SoC (никогда, не в этой жизни)

## Связанные
- ADR-035 (Roadmap 2026)
- ADR-036 (Creative & Craftsman)
- ADR-039 (Distributed Aura)
