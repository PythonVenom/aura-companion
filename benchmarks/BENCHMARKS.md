# Aura Benchmarks — v0.9.0-alpha

Метрики голосового цикла. Baseline на старом железе (2016), чтобы показать
масштаб ожидаемого ускорения на AMD Strix Halo.

## Hardware

| | |
|---|---|
| **CPU** | Intel Coffee Lake-H, 6c/12t, 4.1 GHz |
| **GPU** | NVIDIA GTX 1070M, 8 GB VRAM, driver 470 |
| **RAM** | 31 GB |
| **OS** | Arch Linux, KDE Plasma 6, PipeWire |

## LLM (Ollama qwen2.5:7b-instruct-q4_K_M)

| Метрика | Значение |
|---|---|
| Prompt eval rate | ~36 tok/s |
| **Eval rate (generation)** | **~48 tok/s** |
| Стабильность (3 прогона) | 46.8 / 48.5 / 49.7 tok/s |

## ASR (T-one streaming CTC, 8 kHz)

| Метрика | Значение |
|---|---|
| Model load | 2063 ms (однократно при старте) |
| **Inference** | **290 ms** (фраза 3.85 сек) |
| **RTF (real-time factor)** | **0.075** → 13× быстрее real-time |

## TTS (Piper ru_RU-irina-medium)

| Метрика | Значение |
|---|---|
| Cold start (с загрузкой модели) | 1712–1926 ms |
| Синтез (оценка, модель в памяти) | ~300 ms |
| Output | 170 KB WAV |

## Голосовой цикл (end-to-end, оценка)

Для короткой команды «Аура, который час»:

| Этап | ms |
|---|---|
| ASR (3.85s → text) | 290 |
| LLM (prompt → first token) | ~300 |
| LLM (генерация 5-10 tok) | ~150 |
| TTS (синтез 1.5s) | ~300 |
| **Итого** | **~1050 ms** |

**Целевое:** <2000 ms. **Достигнуто:** ~1050 ms.

## Ожидание на AMD Strix Halo

Strix Halo: 16 Zen 5 ядер + RDNA 3.5 iGPU + unified memory 32–128 GB.

| Метрика | Сейчас (2016) | Ожидаем на Strix Halo |
|---|---|---|
| LLM 7B Q4 | 48 tok/s | **250+ tok/s** (5×) |
| LLM 32B Q4 | не влезает в VRAM | **50–80 tok/s** (unified memory) |
| ASR RTF | 0.075 | **<0.03** |
| Power (LLM) | ~90 W (GTX 1070M) | **40–55 W** |

## Запуск

    ./benchmarks/run_all.sh
    ./benchmarks/run_tts.sh
    ./benchmarks/run_asr.py /tmp/aura_tts_bench.wav

Результаты: `benchmarks/results/`
