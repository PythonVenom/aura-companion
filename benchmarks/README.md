# Aura Benchmarks

Метрики голосового цикла Aura. Baseline — старое железо (2016), чтобы
показать масштаб ожидаемого ускорения на AMD Strix Halo.

## Что мерим

| Метрика | Описание | Целевое |
|---|---|---|
| **ASR latency** | T-one: слово → текст | <300 ms |
| **LLM TTFT** | Time To First Token | <500 ms |
| **LLM eval rate** | tokens/sec на генерации | >30 tok/s |
| **TTS latency** | Piper: текст → звук | <200 ms |
| **End-to-end** | «Аура, время» → ответ | <2 сек |
| **RAM/VRAM** | Потребление памяти | <8 GB |

## Запуск

    ./benchmarks/run_all.sh

Результат: `benchmarks/results/results-YYYYMMDD-HHMMSS.md`

## Baseline (27.09.2026)

- **CPU:** Intel Coffee Lake-H (6c/12t, 4.1 GHz)
- **GPU:** NVIDIA GTX 1070M, 8 GB VRAM, driver 470
- **LLM:** 48 tok/s (qwen2.5:7b-instruct-q4_K_M)

## Ожидание на AMD Strix Halo

- LLM 7B Q4: 5–10× быстрее (250+ tok/s)
- LLM 32B Q4: 50–80 tok/s (unified memory)
- Power: 40–55 W vs 90 W у GTX 1070M
