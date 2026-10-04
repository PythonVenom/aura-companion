# ADR-024: Android Deployment

**Дата:** 2026-09-28
**Статус:** Принято

## Контекст

Врач, массажист, незрячий — у всех смартфон Android.
Коробку домой не всегда можно поставить.

## Решение

**Aura Android via Termux** — Python-стек в Termux + termux-api.

### Что работает

- Python 3.12 (Termux)
- Vosk / sherpa-onnx (ASR on-device)
- termux-api: TTS, микрофон, уведомления
- RAG через ChromaDB
- Сетевые агенты (погода, время, будильник)

### Что НЕ работает

- Ollama (Android не поддерживается)
- PipeWire, systemd
- Firefox bridge (нет native messaging)
- MPRIS

### LLM варианты

1. **Aura Lite** — без LLM (rule-based + RAG) — рекомендовано
2. **llama.cpp** — ARM-сборка (медленно)
3. **Удалённый API** — облако (нарушает приватность)

Для врача — **Lite** (ADR-025). Полноценно — коробка N100/Pi 5 дома.

## Требования

- RAM: 4+ ГБ
- Android 10+
- Termux + Termux:API

## Связанные

- ADR-025 (Aura Lite)
- ADR-022 (cross-platform)
