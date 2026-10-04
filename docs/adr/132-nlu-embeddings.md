# ADR-132: NLU for RouteTree (Embeddings Intent)

**Статус:** Accepted
**Дата:** 2026-10-03

## Наука

- Reimers, N. & Gurevych, I. (2019). Sentence-BERT. EMNLP.
- Devlin, J. et al. (2019). BERT. NAACL.

## Решение

Гибрид: regex (RouteTree) → embedding если regex не сработал.
Embedding: nomic-embed-text через Ollama. Порог 0.55.
Кэш: 500 записей LRU.

## Интенты
music / time / power / app / browser / control / care

## Ссылки
- ADR-122 (Memory)
- ADR-131 (Meta)
