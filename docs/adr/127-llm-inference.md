# ADR-127: LLM Inference Upgrade

**Статус:** Accepted
**Дата:** 2026-10-02

## Контекст

Сейчас: urllib.request → Ollama /api/chat, sync, без batching, без streaming.
Прямой loss 3-10x по throughput и latency.

## Наука

- vLLM: Kwon, W. et al. (2023). Efficient Memory Management for LLM Serving with PagedAttention. SOSP.
- Orca: Yu, G-I. et al. (2022). Continuous Batching.
- SGLang: Zheng, L. et al. (2023). Structured Generation Language.
- Speculative Decoding: Leviathan, Y. et al. (2023). Fast Inference via Speculative Decoding. ICML.
- Prompt Cache: Gim, I. et al. (2023). Prompt Cache: Modular Attention Reuse.

## Решение

Слой aura/core/inference/ — абстракция над Ollama / vLLM / llama.cpp:

    class InferenceBackend:
        def generate(prompt, **kw) -> str
        def stream(prompt, **kw) -> Iterator[str]
        def batch(prompts, **kw) -> list[str]

## Backends

1. OllamaBackend (текущий) — sync, fallback
2. OllamaStreamingBackend — через /api/chat stream=true
3. VLLMBackend (v5.0) — если есть GPU
4. LlamaCppBackend — CPU-optimized, quantization

## Фичи v4.0

- Streaming: ответ токен-за-токеном → голос начинается быстрее
- Prompt cache: system prompt кэшируется через Ollama keep_alive
- Constrained generation: JSON schema через Ollama format=json
- Batching: несколько параллельных запросов через asyncio.gather

## Отложено на v5

- Speculative decoding (нужен draft model)
- PagedAttention / vLLM (нужен GPU)
- Continuous batching

## Метрики

- TTFT (Time To First Token) — цель < 500ms
- TPS (Tokens Per Second) — цель > 30 (CPU)
- Latency p95 — цель < 3s

## Последствия

- (+) голос отвечает быстрее
- (+) параллельные вызовы
- (+) structured output
- (−) +1 слой абстракции
- (−) streaming меняет API callers

## Ссылки

- ADR-123 (ReAct), ADR-124 (Context), ADR-128 (Eval)
