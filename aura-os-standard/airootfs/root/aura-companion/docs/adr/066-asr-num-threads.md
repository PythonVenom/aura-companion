# ADR-066: ASR num_threads и idle CPU

**Дата:** 2026-10-01
**Статус:** Proposed

## Контекст

Bug 66: `aura_main.py` в простое ест 40-65% CPU.
`perf record` показал: 48.95% времени в
`onnxruntime::concurrency::SpinPause()`.
Это thread pool ONNX Runtime (внутри sherpa-onnx) крутит
spin-wait вместо сна.

В `listener.py:56` стоит `num_threads=2`. Ни ADR, ни
комментария, почему 2. Гипотеза: лишний поток в пуле
жжёт CPU в простое.

## Решение (proposed)

- `num_threads=2` → `num_threads=1`
- Пул не создаётся, spin-wait нет.
- Замер: CPU упал с 44% до 19% (среднее за 10 мин).

## Последствия

- Если работает — Принято, коммит.
- Если не работает — Rejected, следующая гипотеза:
  monkey-patch C++ sherpa-onnx, или замена модели.

## Связи

- Bug 66 (JOURNAL)
- perf-профиль: SpinPause 48.95%
