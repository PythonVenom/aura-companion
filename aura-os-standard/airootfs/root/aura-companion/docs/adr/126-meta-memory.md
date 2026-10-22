# ADR-126: Meta-Memory (Self-Reflective Confidence)

**Статус:** Accepted
**Дата:** 2026-10-02

## Контекст

Aura не знает, знает ли она. Может галлюцинировать с уверенностью.
Meta-memory — слой, который оценивает надёжность своих знаний.

## Наука

- MetaMem (2026). Self-Reflective Memory with Confidence Scoring.
- Kadavath, S. et al. (2022). Language Models (Mostly) Know What They Know. Anthropic.
- Lin, S. et al. (2022). Teaching Models to Express Uncertainty (TruthfulQA).
- Kuhn, L. et al. (2023). Semantic Uncertainty. ICLR.

Идеи:
1. LLM имеет внутренний сигнал уверенности
2. Его можно калибровать
3. При низкой уверенности — Aura говорит «не помню точно»

## Решение

При записи факта в Semantic/Social:
- LLM оценивает confidence (0..1)
- Храним вместе с фактом
- Re-оценка при каждом recall

При recall:
- confidence > 0.8 → уверенный ответ
- 0.5-0.8 → «кажется, что ...»
- < 0.5 → «не уверена, но возможно ...»
- 0 → «не помню»

## Формула

    confidence = α * extraction_score
               + β * evidence_count
               + γ * recency_factor
               + δ * consistency_with_prior

Веса подбираются по калибровочному набору.

## Калибровка

100 пар (вопрос → answered?) → ECE (Expected Calibration Error).
Цель: ECE < 0.05 (Brier score).

## Последствия

- (+) доверие: Aura не врёт с уверенностью
- (+) self-reflection: «я не знаю, но спрошу батю»
- (+) безопасность: canary от галлюцинаций
- (−) +1 LLM вызов на запись и recall

## Милстоун

v5.0 (не v4.0).

## Ссылки

- Kadavath (2022). Anthropic.
- Lin (2022). TruthfulQA.
- ADR-122, ADR-125, ADR-128
