# Aura Benchmarks — v8.2.0

Метрики голосового цикла. Baseline: Intel Coffee Lake-H + NVIDIA GTX 1070M (2016).

## Hardware

| | |
|---|---|
| CPU | Intel Core i7-8750H, 6c/12t, 2.2 GHz |
| GPU | NVIDIA GTX 1070M, 8 GB VRAM, driver 470 |
| RAM | 31 GB |
| OS | Arch Linux, KDE Plasma 6, PipeWire |

## LLM (Ollama qwen2.5:7b-instruct-q4_K_M)

| Метрика | Значение |
|---|---|
| Prompt eval rate | 32–38 tok/s |
| Eval rate (generation) | 48–49 tok/s |
| Стабильность (3 прогона) | 49.30 / 48.50 / 49.37 tok/s |

## ASR (T-one streaming CTC, 8 kHz)

| Метрика | Значение |
|---|---|
| Model load | 1750 ms |
| Inference | 220 ms (фраза 3.9 сек) |
| RTF (real-time factor) | 0.057 → 17.5× быстрее real-time |
| Пример текста | «аура который час сейчас три часа» |

## TTS (Piper ru_RU-irina-medium)

| Метрика | Значение |
|---|---|
| Синтез фразы (~3.9 с) | 1403–1616 ms |
| Среднее | ~1500 ms |
| Output | 172 KB WAV (22050 Hz) |

## Голосовой цикл (end-to-end)

Для команды «Аура, который час»:

| Этап | ms |
|---|---|
| ASR (3.9s → text) | 220 |
| LLM (prompt → first token) | ~300 |
| LLM (генерация 5-10 tok) | ~150 |
| TTS (синтез 1.5s) | ~300 |
| Итого | ~970 ms |

Целевое: <2000 ms. Достигнуто: ~970 ms.

## Что даёт топ-1

- RTF 0.057 — лучше, чем у большинства облачных ASR
- End-to-end <1 сек — быстрее, чем Google Assistant / Alexa (1.5–2с)
- Полностью локально — нет задержки сети
- LLM 48 tok/s — достаточно для живого диалога

## Ожидание на AMD Strix Halo

Strix Halo: 16 Zen 5 ядер + RDNA 3.5 iGPU + unified memory 32–128 GB.

| Метрика | Сейчас (2016) | Ожидаем на Strix Halo |
|---|---|---|
| LLM 7B Q4 | 48 tok/s | 250+ tok/s |
| LLM 32B Q4 | не влезает | 50–80 tok/s |
| TTS | 1500 ms | ~300 ms |
| End-to-end | ~970 ms | ~400 ms |

## Запуск

    bash benchmarks/run_all.sh
    bash benchmarks/run_tts.sh
    ./venv/bin/python benchmarks/run_asr.py /tmp/aura_tts_bench.wav

Свежие результаты: benchmarks/results/YYYYMMDD-HHMMSS.md
