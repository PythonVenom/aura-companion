# ADR-152: Aura Tier 0 — Minimal Core (Science 0)

**Статус:** Accepted
**Дата:** 2026-10-03

## Контекст

Elder care на слабом железе. Full Aura не влезает.

## Наука (полные референсы)

1. Warden, P. (2018). Speech Commands: A Dataset for Limited-Vocabulary
   Speech Recognition. arXiv:1804.03209.

2. Zhang, Y., Suda, N., Lai, L., & Chandra, V. (2017). Hello Edge:
   Keyword Spotting on Microcontrollers. arXiv:1711.07128.

3. Joulin, A., Grave, E., Bojanowski, P., & Mikolov, T. (2016).
   Bag of Tricks for Efficient Text Classification. EACL 2017.
   arXiv:1607.01759. (fastText)

4. Ma, S., Wang, H., et al. (2024). The Era of 1-bit LLMs: All Large
   Language Models are in 1.58 Bits. arXiv:2402.17764. (BitNet)

5. Weizenbaum, J. (1966). ELIZA — A Computer Program For the Study of
   Natural Language Communication Between Man and Machine.
   Communications of the ACM, 9(1), 36-45.

## Решение

Tier 0 = минимальный уровень:
- ASR: Keyword Spotting (DS-CNN, ~20 KB)
- NLU: fastText-style intent classifier (~1 MB, 24 интента)
- Dispatch: templates (~10 KB, 20 шаблонов)
- TTS: Piper low (20 MB) + pre-recorded
- LLM: НЕТ (fallback если RAM ≥ 4 GB)
- Memory: 6 слоёв
- RAM бюджет: < 100 MB
- Latency: < 600 ms

## Метрики

| Метрика | Цель |
|---------|------|
| RAM | < 100 MB |
| Latency (90% команд) | < 10 ms |
| Latency (p95) | < 600 ms |
| CPU Pentium 6405U | < 20% |
| Работает без сети | ✅ |
| Работает без GPU | ✅ |

## Ссылки
- ADR-139, ADR-151, ADR-153
