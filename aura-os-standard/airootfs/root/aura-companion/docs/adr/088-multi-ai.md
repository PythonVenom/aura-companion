# ADR-088: Multi-AI Orchestration

**Дата:** 2026-10-02
**Статус:** Проект

## Контекст
Пользователь: «Напили задачи Дипсику, Qwen, ChatGPT. Собери отчёт.
Я купаться.» — AI-to-AI медиатор.

## Решение
Aura = голосовой медиатор между user и внешними ИИ.
- Task Queue (SQLite + asyncio)
- Egress Broker (ADR-091) — фильтр исходящего
- Logbook — все обращения
- MCP client/server (Anthropic standard)
- Voice interface

## Технологии
- HTTP: httpx, requests
- OpenAI: openai SDK
- Qwen: dashscope
- DeepSeek: httpx
- Telegram: python-telegram-bot
- MCP: mcp Python SDK

## Правила
1. Local LLM — основа (всегда)
2. Внешние AI — per-task, с подтверждением
3. Egress Broker фильтрует
4. Logbook логирует
5. Бюджет: AURA_API_BUDGET=100₽/день
6. Whitelist API

## Порядок (ToC)
1. ADR-088
2. Logbook — есть
3. Egress Broker
4. DeepSeek API (MVP)
5. Task Queue
6. Мульти-API
7. MCP

## YAGNI
- 10 API сразу (сначала DeepSeek)
- Автономные цепочки без confirm

## Ссылки
ADR-084, ADR-054 (egress broker), ADR-091
