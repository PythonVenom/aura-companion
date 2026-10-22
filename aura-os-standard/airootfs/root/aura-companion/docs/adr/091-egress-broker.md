# ADR-091: Egress Broker

**Дата:** 2026-10-02
**Статус:** Проект

## Контекст
Плагины ходят в облако (DeepSeek, Qwen). Нужен фильтр — приватность табу.

## Решение
Egress Broker между Aura и внешним AI.
- Whitelist endpoint
- Только текст задачи, никаких user_data
- Бюджет per-task
- Логирование в Logbook
- Опционален (user может отключить → прямой доступ)

## Поток
Aura → broker → cloud AI → ответ → broker → Aura
       ↑
       фильтр: device_state, никаких user_profile

## Правила
1. Локально по умолчанию
2. Cloud — per-task, с подтверждением
3. Broker фильтрует всё
4. Env: AURA_EGRESS_BROKER=1 (включить)
5. AURA_SMART_HOME_CLOUD=0 (запрет облака)

## YAGNI
- Не пишем свой proxy (httpx + фильтр)
- Не делаем DLP (data loss prevention) — overkill

## Ссылки
ADR-054 (односторонняя видимость), ADR-088, ADR-090
