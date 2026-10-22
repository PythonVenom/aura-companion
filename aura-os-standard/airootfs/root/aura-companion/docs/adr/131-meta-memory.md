# ADR-131: Meta-Memory (Confidence & Calibration)

**Статус:** Accepted
**Дата:** 2026-10-02

## Наука

- Kadavath, S. et al. (2022). Language Models (Mostly) Know What They Know. Anthropic. arXiv:2207.05221
- Lin, S. et al. (2022). Teaching Models to Express Uncertainty. ACL.
- Kuhn, L. et al. (2023). Semantic Uncertainty. ICLR.
- Guo, C. et al. (2017). On Calibration of Modern Neural Networks. ICML.

## Решение

10-й слой памяти — Meta. Оценивает уверенность каждого факта:

    confidence = alpha * extraction_score
               + beta  * evidence_count_norm
               + gamma * recency_factor
               + delta * consistency

При recall:
- > 0.8   — уверенный ответ
- 0.5-0.8 — "кажется, что ..."
- < 0.5   — "не уверена, но возможно ..."
- = 0     — "не помню"

## Калибровка

ECE (Expected Calibration Error) < 0.05. Замер на 100 парах.

## Файлы

- aura/core/memory/meta.py — MetaMemory
- Регистрируется как 10-й слой
